"""Platform capability probes -- stdlib only, no POSIX emulation.

Windows genuinely lacks two POSIX primitives the storage/artifact layer
otherwise relies on:

- Directory fsync: crash-durability of a rename/unlink depends on fsyncing
  the containing directory's own file descriptor. Windows' os.open() cannot
  open a directory this way at all (there is no ReplaceFile/
  FlushFileBuffers wrapper attempted here -- that would be emulating POSIX
  durability semantics, which this project deliberately does not do).
- Private (0600/0700) file/directory modes: os.chmod on Windows can only
  toggle the read-only attribute; it cannot restrict access to the owning
  user the way POSIX permission bits do, and st_mode always reads back as
  fully open regardless of the mode passed to mkdir()/os.open().

Both are exposed as capability probes (hasattr / os.name), never as
try/except around the primitive itself -- an unsupported operation must be
visibly unsupported, not silently "succeed" after failing.

A third mismatch is not a missing primitive but a dangerous reinterpretation
of one: the POSIX pid-liveness idiom os.kill(pid, 0) is not portable, because
signal 0 collides with signal.CTRL_C_EVENT on Windows (see pid_exists below).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

# os.O_DIRECTORY exists exactly where os.open() can open a directory fd for
# fsync -- present on POSIX, absent on Windows.
SUPPORTS_DIRECTORY_FSYNC = hasattr(os, "O_DIRECTORY")

# POSIX permission bits (owner/group/other rwx) are only a real privacy
# guarantee on os.name == "posix"; on Windows os.chmod cannot enforce them.
SUPPORTS_PRIVATE_FILE_MODE = os.name == "posix"

# Only Windows applies CRLF translation / Ctrl-Z truncation to file
# descriptors opened without O_BINARY. This is 0 (a no-op flag) on
# platforms where os.O_BINARY does not exist.
O_BINARY = getattr(os, "O_BINARY", 0)

_REPARSE_POINT_ATTR = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _ERROR_ACCESS_DENIED = 5

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)


def platform_capabilities() -> dict[str, bool]:
    """The durability/privacy guarantees available on this host.

    Persisted verbatim into new session state (see state.new_state) so a
    reader of a package produced on a degraded host can tell, after the
    fact, which guarantees actually held for that session.
    """

    return {
        "directory_fsync": SUPPORTS_DIRECTORY_FSYNC,
        "private_file_mode": SUPPORTS_PRIVATE_FILE_MODE,
    }


def is_symlink_or_reparse_point(path: Path) -> bool:
    """True if path is a symlink, or (on Windows) any other reparse point.

    pathlib.Path.is_symlink() / os.path.islink() correctly detect POSIX
    symlinks and Windows symbolic links: both are tagged
    IO_REPARSE_TAG_SYMLINK, which os.lstat() surfaces as stat.S_ISLNK.

    They do NOT detect NTFS directory junctions (IO_REPARSE_TAG_MOUNT_POINT):
    a junction is a reparse point but carries a different tag, so S_ISLNK is
    false for one even though following it walks somewhere else entirely.
    A junction can still redirect a supposedly-confined directory (a
    session directory, raw/, provider_spool/) elsewhere, so this also
    checks the reparse-point file attribute bit on Windows -- stdlib only
    (os.lstat's st_file_attributes), no ctypes, no pywin32. st_file_attributes
    does not exist on POSIX stat results, so this is a no-op there.
    """

    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & _REPARSE_POINT_ATTR)


def pid_exists(pid: int) -> bool:
    """True if `pid` identifies a currently-running process.

    os.kill(pid, 0) is the POSIX idiom for this -- signal 0 is a true
    null signal there, delivered to nobody, used only to probe whether the
    kernel will accept the pid/permission pair. It is not safe to reuse on
    Windows: signal.CTRL_C_EVENT == 0, so CPython's os.kill() special-cases
    signal 0 (and 1, CTRL_BREAK_EVENT) by calling
    GenerateConsoleCtrlEvent(sig, pid) instead of any kind of existence
    check. For a live pid that silently asks the OS to deliver a real
    console control event to whatever process group `pid` happens to
    resolve to; for a dead pid it raises OSError (WinError 87, "the
    parameter is incorrect") rather than ProcessLookupError, since `pid` is
    being interpreted as a console process-group id, not a target to look
    up. Query the process table directly instead.
    """

    if pid <= 0:
        return False
    if os.name == "nt":
        handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            _kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() == _ERROR_ACCESS_DENIED
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True
