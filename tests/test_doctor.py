from __future__ import annotations

import unittest

from scripts.doctor import version_at_least


class DoctorVersionTests(unittest.TestCase):
    def test_missing_version_is_incompatible(self) -> None:
        self.assertFalse(version_at_least(None, "2.0.0"))

    def test_current_major_is_compatible(self) -> None:
        self.assertTrue(version_at_least("2.11.0", "2.0.0"))

    def test_legacy_major_is_incompatible(self) -> None:
        self.assertFalse(version_at_least("1.70.0", "2.0.0"))

    def test_prerelease_suffix_does_not_break_comparison(self) -> None:
        self.assertTrue(version_at_least("2.0.0rc1", "2.0.0"))


if __name__ == "__main__":
    unittest.main()
