#!/usr/bin/env python3
"""Deep Research CLI — multi-provider research engine.

Providers:
  sonar       Perplexity sonar-pro             — quick grounded answer (seconds, ~$0.01)
  cascade     4 parallel sonar probes           — scout: direct/counter/landscape/falsifier (~$0.10-0.15)
  scholar     Semantic Scholar paper search     — academic literature list (seconds, free)
  perplexity  Perplexity sonar-deep-research   — async deep research (2-5 min, ~$0.5-1)
  openai      OpenAI o3 / o4-mini deep research — async deep research (5-30 min, ~$0.4-8)
  gemini      Gemini Deep Research agent        — background interaction (2-10 min)
  deepseek    DeepSeek v4 processor             — merge/extract/rewrite over --files (~free)

Usage:
  python deep_research.py [--provider P] [--effort E] [--model M] [--timeout-min N] [--ledger FILE] "question"
  python deep_research.py --provider deepseek --files r1.md --files r2.md "merge these into a claims table"
  python deep_research.py --resume "openai:resp_abc123"

Output: single JSON object on stdout:
  {query, provider, model, effort, report_path, report, usage, cost_estimate_usd, wall_time_s}
Progress and the resume token go to stderr. Reports are saved to <cwd>/reports/.

API keys (first hit wins): process env > nearest .env from cwd upward > <skill>/.env
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

def _fix_console_encoding():
    """Windows cp950 等 console 的 UTF-8 包裝 — 只在 CLI 模式呼叫，import 無副作用。"""
    for name in ("stdout", "stderr"):
        s = getattr(sys, name)
        if s and hasattr(s, "buffer"):
            setattr(sys, name, io.TextIOWrapper(s.buffer, encoding="utf-8", errors="replace"))


SKILL_DIR = Path(__file__).resolve().parents[1]
PPLX_BASE = "https://api.perplexity.ai"
OPENAI_BASE = "https://api.openai.com"

# USD per 1M tokens (input, output); web search $10 per 1k calls. OpenAI returns no
# cost field, so this is an estimate — Perplexity responses carry their own total_cost.
OPENAI_PRICE = {"o3-deep-research": (10.0, 40.0), "o4-mini-deep-research": (2.0, 8.0)}
OPENAI_SEARCH_PER_1K = 10.0
OPENAI_TOOL_CAP = {"minimal": 10, "low": 20, "medium": 40, "high": None}


def _load_env():
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv(usecwd=True))
    load_dotenv(SKILL_DIR / ".env")


def _require_key(name: str) -> str:
    key = os.getenv(name)
    if not key:
        raise RuntimeError(f"{name} 未設定 — 放在專案 .env 或 {SKILL_DIR / '.env'}")
    return key


def _log(msg: str):
    print(f"[deep] {msg}", file=sys.stderr)


class JobError(RuntimeError):
    """已提交、可續跑的 job 出錯 — resume token 隨錯誤結構化帶出，避免重付。"""

    def __init__(self, message: str, resume: str = None):
        super().__init__(message)
        self.resume = resume


# ── Perplexity ────────────────────────────────────────────────────────────────

def _pplx_headers():
    return {"Authorization": f"Bearer {_require_key('PERPLEXITY_API_KEY')}",
            "Content-Type": "application/json"}


def _pplx_extract(data: dict, model: str, effort) -> dict:
    resp = data["response"]
    usage = resp.get("usage") or {}
    cost = (usage.get("cost") or {}).get("total_cost")
    sources = resp.get("search_results") or [{"url": u} for u in (resp.get("citations") or [])]
    return {
        "model": model,
        "effort": effort,
        "report_text": resp["choices"][0]["message"]["content"],
        "usage": usage,
        "cost_estimate_usd": round(cost, 4) if cost is not None else None,
        "sources": sources,
    }


def _pplx_poll(request_id: str, timeout_min: float) -> dict:
    import requests

    headers = _pplx_headers()
    token = f"perplexity:{request_id}"
    t0 = time.monotonic()
    while True:
        elapsed = time.monotonic() - t0
        if elapsed > timeout_min * 60:
            raise JobError(f"輪詢超過 {timeout_min:.0f} 分鐘上限 — 稍後可 --resume \"{token}\"", resume=token)
        r = requests.get(f"{PPLX_BASE}/v1/async/sonar/{request_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            raise JobError(f"poll 失敗 HTTP {r.status_code}: {r.text[:300]}", resume=token)
        data = r.json()
        status = data.get("status", "UNKNOWN")
        _log(f"狀態：{status}（{int(elapsed)}s）")
        if status == "COMPLETED":
            return data
        if status == "FAILED":
            raise JobError(f"研究失敗：{data.get('error_message', '（無錯誤訊息）')}", resume=token)
        time.sleep(15)


def call_perplexity(query: str, effort: str, model, timeout_min, files=None) -> dict:
    import requests

    model = model or "sonar-deep-research"
    payload = {"request": {"model": model,
                           "messages": [{"role": "user", "content": query}],
                           "reasoning_effort": effort}}
    _log(f"啟動研究（perplexity/{model} effort={effort}）")
    r = requests.post(f"{PPLX_BASE}/v1/async/sonar", headers=_pplx_headers(), json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"submit 失敗 HTTP {r.status_code}: {r.text[:300]}")
    request_id = r.json()["id"]
    _log(f"resume token: perplexity:{request_id}")
    data = _pplx_poll(request_id, timeout_min or 20)
    return _pplx_extract(data, model, effort)


def call_sonar(query: str, effort: str, model, timeout_min, files=None) -> dict:
    """Quick tier — synchronous grounded answer, no polling."""
    import requests

    model = model or "sonar-pro"
    _log(f"快查（{model}）")
    r = requests.post(f"{PPLX_BASE}/chat/completions", headers=_pplx_headers(),
                      json={"model": model, "messages": [{"role": "user", "content": query}]},
                      timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    usage = data.get("usage") or {}
    cost = (usage.get("cost") or {}).get("total_cost")
    sources = data.get("search_results") or [{"url": u} for u in (data.get("citations") or [])]
    return {
        "model": model,
        "effort": None,
        "report_text": data["choices"][0]["message"]["content"],
        "usage": usage,
        "cost_estimate_usd": round(cost, 4) if cost is not None else None,
        "sources": sources,
    }


# ── 探針瀑布（scout）──────────────────────────────────────────────────────────

CASCADE_FRAMINGS = [
    ("direct", "{q}"),
    ("counter", "What is the strongest counterargument or opposing evidence to the following? {q}"),
    ("landscape", "What are the key terms, main players, and notable recent developments relevant to: {q}"),
    ("falsifier", "What specific evidence, if it existed, would most change the answer to: {q}"),
]


def call_cascade(query: str, effort: str, model, timeout_min, files=None) -> dict:
    """Scout：四個框架並行快查，一次呼叫回齊 — 取代多個背景 sonar call 的編排負擔。"""
    from concurrent.futures import ThreadPoolExecutor

    _log(f"探針瀑布：{len(CASCADE_FRAMINGS)} 發並行（sonar-pro）")

    def one(framing):
        name, tpl = framing
        try:
            return name, call_sonar(tpl.format(q=query), effort, model, timeout_min), None
        except Exception as e:  # 單發失敗不拖垮整組
            return name, None, str(e)

    with ThreadPoolExecutor(max_workers=len(CASCADE_FRAMINGS)) as ex:
        results = list(ex.map(one, CASCADE_FRAMINGS))

    parts, sources, seen, usage, failures = [], [], set(), {}, {}
    total_cost = 0.0
    for name, r, err in results:
        if err:
            failures[name] = err
            parts.append(f"## 探針：{name}\n\n（失敗：{err}）")
            continue
        parts.append(f"## 探針：{name}\n\n{r['report_text']}")
        usage[name] = r.get("usage", {})
        total_cost += r.get("cost_estimate_usd") or 0.0
        for s in r.get("sources", []):
            url = s.get("url", "")
            if url and url not in seen:
                seen.add(url)
                sources.append(s)

    if len(failures) == len(CASCADE_FRAMINGS):
        raise RuntimeError(f"cascade 全數探針失敗：{failures}")
    if failures:
        usage["_failures"] = failures
    return {"model": f"sonar-pro ×{len(CASCADE_FRAMINGS)}", "effort": None,
            "report_text": "\n\n".join(parts),
            "usage": usage, "cost_estimate_usd": round(total_cost, 4), "sources": sources}


# ── Semantic Scholar ──────────────────────────────────────────────────────────

S2_FIELDS = "title,year,abstract,citationCount,authors,url,openAccessPdf,tldr"
S2_LIMIT = {"minimal": 5, "low": 10, "medium": 20, "high": 40}


def call_scholar(query: str, effort: str, model, timeout_min, files=None) -> dict:
    """Academic literature search. Query = keyword phrase, not a question. 1 req/sec."""
    import requests

    key = os.getenv("S2_API_KEY")
    headers = {"x-api-key": key} if key else {}
    if not key:
        _log("無 S2_API_KEY — 走共享池（限速更嚴、可能 429）")
    limit = S2_LIMIT.get(effort, 20)
    params = {"query": query, "limit": limit, "fields": S2_FIELDS}
    _log(f"文獻檢索（semantic scholar, limit={limit}）")
    r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
                     headers=headers, params=params, timeout=30)
    if r.status_code == 429:  # S2 rate limit: 1 req/sec cumulative — retry once
        time.sleep(1.5)
        r = requests.get("https://api.semanticscholar.org/graph/v1/paper/search",
                         headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    papers = data.get("data") or []

    lines = [f"## 文獻檢索結果（{len(papers)} / 共 {data.get('total', '?')} 篇，按相關性）\n"]
    for i, p in enumerate(papers, 1):
        authors = ", ".join(a.get("name", "") for a in (p.get("authors") or [])[:4])
        if len(p.get("authors") or []) > 4:
            authors += " et al."
        tldr = (p.get("tldr") or {}).get("text") or (p.get("abstract") or "")[:300]
        pdf = (p.get("openAccessPdf") or {}).get("url")
        lines.append(f"\n{i}. **{p.get('title', '?')}**（{p.get('year', '?')}）— 引用 {p.get('citationCount', 0)}\n")
        lines.append(f"   {authors}\n")
        if tldr:
            lines.append(f"   {tldr}\n")
        link = f"   [S2]({p.get('url', '')})"
        if pdf:
            link += f" ｜ [PDF]({pdf})"
        lines.append(link + "\n")

    return {"model": "s2-graph/paper-search", "effort": effort,
            "report_text": "".join(lines),
            "usage": {"total_results": data.get("total"), "returned": len(papers)},
            "cost_estimate_usd": 0.0, "sources": []}


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _openai_headers():
    return {"Authorization": f"Bearer {_require_key('OPENAI_API_KEY')}",
            "Content-Type": "application/json"}


def _openai_extract(data: dict, model: str, effort) -> dict:
    text, sources, searches, seen = "", [], 0, set()
    for item in data.get("output", []):
        kind = item.get("type")
        if kind == "web_search_call":
            searches += 1
        elif kind == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")
                    for a in c.get("annotations") or []:
                        url = a.get("url", "")
                        if a.get("type") == "url_citation" and url and url not in seen:
                            seen.add(url)
                            sources.append({"title": a.get("title") or url, "url": url})
    usage = dict(data.get("usage") or {})
    usage["num_web_searches"] = searches
    p_in, p_out = OPENAI_PRICE.get(model, (0.0, 0.0))
    cost = ((usage.get("input_tokens") or 0) * p_in / 1e6
            + (usage.get("output_tokens") or 0) * p_out / 1e6
            + searches * OPENAI_SEARCH_PER_1K / 1e3)
    return {
        "model": model,
        "effort": effort,
        "report_text": text,
        "usage": usage,
        "cost_estimate_usd": round(cost, 4),
        "sources": sources,
    }


def _openai_poll(resp_id: str, timeout_min: float) -> dict:
    import requests

    headers = _openai_headers()
    token = f"openai:{resp_id}"
    t0 = time.monotonic()
    while True:
        elapsed = time.monotonic() - t0
        if elapsed > timeout_min * 60:
            raise JobError(f"輪詢超過 {timeout_min:.0f} 分鐘上限 — 稍後可 --resume \"{token}\"", resume=token)
        r = requests.get(f"{OPENAI_BASE}/v1/responses/{resp_id}", headers=headers, timeout=30)
        if r.status_code != 200:
            raise JobError(f"poll 失敗 HTTP {r.status_code}: {r.text[:300]}", resume=token)
        data = r.json()
        status = data.get("status", "unknown")
        _log(f"狀態：{status}（{int(elapsed)}s）")
        if status == "completed":
            return data
        if status in ("failed", "cancelled", "incomplete"):
            err = (data.get("error") or {}).get("message", "")
            # incomplete 可能仍有部分產出，--resume 可撈回；failed/cancelled 帶 token 供診斷
            raise JobError(f"研究失敗，狀態 {status}：{err[:300]}", resume=token)
        time.sleep(20)


def call_openai(query: str, effort: str, model, timeout_min, files=None) -> dict:
    import requests

    model = model or ("o3-deep-research" if effort == "high" else "o4-mini-deep-research")
    body = {"model": model, "input": query, "background": True,
            "tools": [{"type": "web_search_preview"}]}
    cap = OPENAI_TOOL_CAP.get(effort)
    if cap:
        body["max_tool_calls"] = cap
    _log(f"啟動研究（openai/{model} effort={effort} tool_cap={cap}）")
    r = requests.post(f"{OPENAI_BASE}/v1/responses", headers=_openai_headers(), json=body, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"submit 失敗 HTTP {r.status_code}: {r.text[:300]}")
    resp_id = r.json()["id"]
    _log(f"resume token: openai:{resp_id}")
    data = _openai_poll(resp_id, timeout_min or 45)
    return _openai_extract(data, model, effort)


# ── Gemini ────────────────────────────────────────────────────────────────────

def _gemini_client():
    from google import genai

    return genai.Client(api_key=_require_key("GEMINI_API_KEY"))


def _gemini_poll(client, interaction_id: str, timeout_min: float):
    token = f"gemini:{interaction_id}"
    t0 = time.monotonic()
    while True:
        elapsed = time.monotonic() - t0
        if elapsed > timeout_min * 60:
            raise JobError(f"輪詢超過 {timeout_min:.0f} 分鐘上限 — 稍後可 --resume \"{token}\"", resume=token)
        interaction = client.interactions.get(interaction_id)
        status = interaction.status
        _log(f"狀態：{status}（{int(elapsed)}s）")
        if status == "completed":
            return interaction
        if status in ("failed", "cancelled"):
            raise JobError(f"研究失敗，狀態：{status}", resume=token)
        time.sleep(15)


def _gemini_extract(interaction, agent: str) -> dict:
    # 新 schema（Interactions API 2026-05+）。文件的 steps[-1] 說法不可靠：實測正文與來源
    # 可能分佈在不同 step，且單一 step 的 text 可拆多個 content part。策略：逐 step 聚合
    # text，優先非 grounding/citation 類 step，再以長度 tie-break。
    steps = getattr(interaction, "steps", None) or []
    candidates = []
    for st in steps:
        label = " ".join(str(getattr(st, a, "") or "") for a in ("type", "name", "title")).lower()
        text = "\n\n".join(c.text for c in (getattr(st, "content", None) or [])
                           if getattr(c, "text", None))
        if text.strip():
            candidates.append((label, text))
    bodyish = [c for c in candidates if not re.search(r"ground|source|citation|search", c[0])]
    # 長報告會拆多個 step（實測 6.6k+14.7k+22.8k 三段）— 按序串接所有實質本體段，
    # 不取最長（會丟前半）；<600 字的段視為 query 回音/狀態訊息排除
    substantial = [c[1] for c in (bodyish or candidates) if len(c[1]) >= 600]
    if substantial:
        report_text = "\n\n".join(substantial)
    else:
        report_text = max(bodyish or candidates, key=lambda c: len(c[1]))[1] if candidates else ""
    if not report_text:  # 舊 schema fallback（萬一）
        report_text = "".join(o.text for o in (getattr(interaction, "outputs", None) or [])
                              if getattr(o, "text", None))
    if not report_text.strip():
        raise RuntimeError("Gemini 回報 completed 但 steps/outputs 都抽不到報告文字")
    # Gemini deep research 把來源以 markdown links 直接寫進報告本體（report_text 末尾），
    # 無獨立結構化 citations 欄位 — sources 留空，避免與內建來源段重複渲染。
    return {"model": agent, "effort": None, "report_text": report_text,
            "usage": {}, "cost_estimate_usd": None, "sources": []}


def call_gemini(query: str, effort: str, model, timeout_min, files=None) -> dict:
    # 呼叫方式與舊版相同（走 **body）；差別在輸出解析（steps schema，見 _gemini_extract）。
    # model 可選 deep-research-preview-04-2026（預設）或 deep-research-max-preview-04-2026。
    client = _gemini_client()
    agent = model or "deep-research-preview-04-2026"
    _log(f"啟動研究（gemini/{agent}）")
    interaction = client.interactions.create(input=query, agent=agent, background=True)
    _log(f"resume token: gemini:{interaction.id}")
    interaction = _gemini_poll(client, interaction.id, timeout_min or 30)
    return _gemini_extract(interaction, agent)


# ── DeepSeek（加工層，不是研究引擎：無檢索、裸答事實幻覺率高）────────────────

def call_deepseek(query: str, effort: str, model, timeout_min, files=None) -> dict:
    import requests

    model = model or "deepseek-v4-pro"
    content = query
    for f in files or []:
        p = Path(f)
        content += f"\n\n=== FILE: {p.name} ===\n{p.read_text(encoding='utf-8', errors='replace')}"
    _log(f"加工（deepseek/{model}，{len(files or [])} 個檔案輸入）")
    # v4-pro 思考模式拒收 temperature/top_p — 不送；長輸出用 max_tokens 上限
    r = requests.post("https://api.deepseek.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {_require_key('DEEPSEEK_API_KEY')}",
                               "Content-Type": "application/json"},
                      json={"model": model,
                            "messages": [{"role": "user", "content": content}],
                            "max_tokens": 16384},
                      timeout=(30, 900))
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    return {"model": model, "effort": None,
            "report_text": data["choices"][0]["message"]["content"],
            "usage": data.get("usage") or {},
            "cost_estimate_usd": None, "sources": []}


PROVIDERS = {"sonar": call_sonar, "cascade": call_cascade, "scholar": call_scholar,
             "perplexity": call_perplexity, "openai": call_openai, "gemini": call_gemini,
             "deepseek": call_deepseek}


# ── Report + entry ────────────────────────────────────────────────────────────

def _slug(query: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", query).strip("-").lower()
    return s[:40].rstrip("-") or "query"


def save_report(provider: str, query: str, result: dict, wall_time_s: float) -> Path:
    reports_dir = Path.cwd() / "reports"
    reports_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 純 CJK query 的 slug 會退化成 "query" — hash(query+pid) 防同秒並行互相覆蓋
    digest = hashlib.sha1(f"{query}|{os.getpid()}".encode("utf-8")).hexdigest()[:6]
    report_path = reports_dir / f"deep_{timestamp}_{_slug(query)}_{digest}.md"

    lines = [
        "# Deep Research 報告\n",
        f"**查詢：** {query}\n",
        f"**時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"**Provider：** {provider}（{result['model']}）\n",
    ]
    if result.get("effort"):
        lines.append(f"**Effort：** {result['effort']}\n")
    lines.append(f"**Wall time：** {wall_time_s:.0f}s\n")
    if result.get("usage"):
        lines.append(f"**Usage：** `{json.dumps(result['usage'], ensure_ascii=False)}`\n")
    if result.get("cost_estimate_usd") is not None:
        lines.append(f"**成本估算：** ${result['cost_estimate_usd']:.4f}\n")
    lines.append("\n---\n\n")
    lines.append(result["report_text"])

    if result.get("sources"):
        lines.append("\n\n---\n\n## Sources\n\n")
        for s in result["sources"]:
            title = (s.get("title") or s.get("url", "")).replace("[", "\\[").replace("]", "\\]")
            url = s.get("url", "").replace(")", "%29")
            date = f"（{s['date']}）" if s.get("date") else ""
            lines.append(f"- [{title}]({url}){date}\n")

    report_path.write_text("".join(lines), encoding="utf-8")
    _log(f"報告已存：{report_path}")
    return report_path


def _finish(provider: str, query: str, result: dict, wall_time_s: float) -> dict:
    report_path = save_report(provider, query, result, wall_time_s)
    return {
        "query": query,
        "provider": provider,
        "model": result["model"],
        "effort": result.get("effort"),
        "report_path": str(report_path),
        "report": result["report_text"],
        "usage": result.get("usage", {}),
        "cost_estimate_usd": result.get("cost_estimate_usd"),
        "wall_time_s": round(wall_time_s, 1),
    }


def _append_ledger(path: str, record: dict):
    """機械 hook：append-only JSONL 帳本 — 記帳不靠 Organizer 自覺；寫入失敗不影響主流程。"""
    try:
        record["ts"] = datetime.now().isoformat(timespec="seconds")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        _log(f"ledger 寫入失敗（不影響結果）：{e}")


def run(provider: str, query: str, effort: str, model, timeout_min, files=None) -> dict:
    t0 = time.monotonic()
    result = PROVIDERS[provider](query, effort, model, timeout_min, files=files)
    return _finish(provider, query, result, time.monotonic() - t0)


def run_resume(token: str, timeout_min) -> dict:
    provider, _, rid = token.partition(":")
    if not rid:
        raise RuntimeError(f'--resume 格式是 "provider:id"，收到：{token}')
    t0 = time.monotonic()
    if provider == "perplexity":
        data = _pplx_poll(rid, timeout_min or 20)
        model = (data.get("response") or {}).get("model") or "sonar-deep-research"
        result = _pplx_extract(data, model, None)
    elif provider == "openai":
        data = _openai_poll(rid, timeout_min or 45)
        result = _openai_extract(data, data.get("model", "?"), None)
    elif provider == "gemini":
        client = _gemini_client()
        interaction = _gemini_poll(client, rid, timeout_min or 30)
        agent = getattr(interaction, "agent", None) or "deep-research-preview-04-2026"
        result = _gemini_extract(interaction, agent)
    else:
        raise RuntimeError(f"provider {provider} 不支援 resume（sonar / scholar / deepseek 為同步呼叫）")
    return _finish(provider, f"[resumed] {token}", result, time.monotonic() - t0)


if __name__ == "__main__":
    _fix_console_encoding()
    parser = argparse.ArgumentParser(description="Deep Research CLI（多 provider）")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default="perplexity")
    parser.add_argument("--effort", choices=["minimal", "low", "medium", "high"], default="medium",
                        help="perplexity: reasoning_effort；openai: high→o3、其餘 o4-mini+tool cap；sonar/gemini 忽略")
    parser.add_argument("--model", default=None, help="覆寫該 provider 的預設 model")
    parser.add_argument("--timeout-min", type=float, default=None, help="輪詢上限（分鐘）")
    parser.add_argument("--resume", default=None, metavar="PROVIDER:ID", help="接手先前的 async job")
    parser.add_argument("--files", action="append", default=None, metavar="FILE",
                        help="deepseek 加工層的檔案輸入（一面旗一個檔，可重複）")
    parser.add_argument("--ledger", default=None, metavar="FILE",
                        help="append-only JSONL 帳本（harness 機械 hook）")
    parser.add_argument("query", nargs="*", help="研究問題")
    args = parser.parse_args()

    if not args.resume and not args.query:
        parser.error("需要 query（或 --resume）")
    if args.files and args.provider != "deepseek":
        parser.error("--files 只支援 --provider deepseek（加工層）— 其他 provider 會默默忽略檔案")

    _load_env()
    try:
        if args.resume:
            out = run_resume(args.resume, args.timeout_min)
        else:
            out = run(args.provider, " ".join(args.query), args.effort, args.model, args.timeout_min, files=args.files)
        if args.ledger:
            _append_ledger(args.ledger, {"provider": out["provider"], "model": out["model"],
                                         "effort": out.get("effort"), "cost_usd": out.get("cost_estimate_usd"),
                                         "wall_s": out.get("wall_time_s"), "artifact": out.get("report_path"),
                                         "query": out["query"][:200]})
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except JobError as e:
        if args.ledger:
            _append_ledger(args.ledger, {"provider": args.provider, "error": str(e)[:300], "resume": e.resume})
        print(json.dumps({"error": str(e), "resume": e.resume}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if args.ledger:
            _append_ledger(args.ledger, {"provider": args.provider, "error": str(e)[:300]})
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
