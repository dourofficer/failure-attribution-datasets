"""Cached client for the local vLLM OpenAI-compatible server (Qwen3.8-27B on :8210)."""
import hashlib
import json
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from common.util import CACHE

BASE_URLS = os.environ.get('LLM_BASE_URLS', 'http://localhost:8210/v1,http://localhost:8211/v1').split(',')
BASE_URL = BASE_URLS[0]
_health = {}  # url -> (ts, queue_depth or None if down)


def _queue_depth(url):
    """running+waiting requests from the server's /metrics; None if the server is down. Cached 3 s."""
    now = time.time()
    ts, q = _health.get(url, (0, None))
    if now - ts < 3:
        return q
    try:
        txt = requests.get(url.replace('/v1', '/metrics'), timeout=2).text
        run = wait = 0.0
        for line in txt.splitlines():
            if line.startswith('vllm:num_requests_running{'):
                run = float(line.rsplit(' ', 1)[1])
            elif line.startswith('vllm:num_requests_waiting{'):
                wait = float(line.rsplit(' ', 1)[1])
        q = run + wait
    except Exception:  # noqa: BLE001
        q = None
    _health[url] = (now, q)
    return q


_inflight = {}  # url -> requests sent by this process and not yet returned (so a burst spreads over servers)


def pick_url():
    """Least-loaded live server (server queue depth + this process's in-flight count); falls back to the first URL."""
    best, best_q = None, None
    for u in BASE_URLS:
        q = _queue_depth(u)
        if q is None:
            continue
        q += _inflight.get(u, 0)
        if best is None or q < best_q:
            best, best_q = u, q
    return best or BASE_URLS[0]
MODEL = os.environ.get('LLM_MODEL', 'qwen3.8-27b')
CACHE_PATH = os.path.join(CACHE, 'llm_cache.sqlite')
_lock = threading.Lock()


def _db():
    con = sqlite3.connect(CACHE_PATH, timeout=60, check_same_thread=False)
    con.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, response TEXT, ts REAL)')
    return con


_con = _db()


def _key(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def chat(messages, max_tokens=4096, temperature=0.0, think=True, top_p=1.0, seed=0, tag=None,
         timeout=1800, retries=3, use_cache=True):
    """Return dict(content, reasoning, usage, cached). Deterministic by default (temperature 0, seed)."""
    payload = {'model': MODEL, 'messages': messages, 'max_tokens': max_tokens, 'temperature': temperature,
               'top_p': top_p, 'seed': seed, 'chat_template_kwargs': {'enable_thinking': bool(think)}}
    key = _key({**payload, 'tag': tag})
    if use_cache:
        with _lock:
            row = _con.execute('SELECT response FROM cache WHERE key=?', (key,)).fetchone()
        if row:
            out = json.loads(row[0])
            out['cached'] = True
            return out
    last = None
    for attempt in range(retries):
        try:
            url = pick_url()
            with _lock:
                _inflight[url] = _inflight.get(url, 0) + 1
            try:
                r = requests.post(url + '/chat/completions', json=payload, timeout=timeout)
            finally:
                with _lock:
                    _inflight[url] = _inflight.get(url, 1) - 1
            r.raise_for_status()
            d = r.json()
            m = d['choices'][0]['message']
            out = {'content': m.get('content') or '', 'reasoning': m.get('reasoning_content') or m.get('reasoning') or '',
                   'usage': d.get('usage'), 'finish_reason': d['choices'][0].get('finish_reason'), 'cached': False}
            if use_cache:
                with _lock:
                    _con.execute('INSERT OR REPLACE INTO cache VALUES (?,?,?)', (key, json.dumps(out, ensure_ascii=False), time.time()))
                    _con.commit()
            return out
        except requests.HTTPError as e:  # noqa: BLE001
            last = e
            if e.response is not None and e.response.status_code == 400:
                break  # prompt too long or malformed: retrying cannot help
            time.sleep(5 * (attempt + 1))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f'LLM call failed after {retries} attempts: {last}')


def chat_many(list_of_messages, workers=8, **kw):
    """Run many chats concurrently (the server batches). Preserves order."""
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda m: chat(m, **kw), list_of_messages))


def extract_json(text):
    """Best-effort: find the last {...} block in text and parse it."""
    import re
    text = text.strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.S)
    cands = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                cands.append(text[start:i + 1])
                start = None
    for c in reversed(cands):
        try:
            return json.loads(c)
        except Exception:  # noqa: BLE001
            continue
    return None


def approx_tokens(text):
    return int(len(text) / 2.6)  # conservative: JSON / code / CJK tokenise at ~2.5 chars per token


def chat_json(messages, max_tokens=8192, think=True, fallback_no_think=True, **kw):
    """chat() + extract_json(); if the answer is unparseable (typically because thinking overran max_tokens),
    retry once without thinking. Returns (parsed_or_None, out). out['fallback'] marks the retry.
    A request that fails outright (e.g. 400: prompt too long) returns (None, out) with out['error'] set."""
    try:
        out = chat(messages, max_tokens=max_tokens, think=think, **kw)
    except RuntimeError as e:
        return None, {'content': '', 'reasoning': '', 'usage': None, 'finish_reason': 'error', 'error': str(e)[:300], 'fallback': False}
    parsed = extract_json(out['content'])
    if parsed is None and fallback_no_think and think:
        out2 = chat(messages, max_tokens=min(max_tokens, 2048), think=False, **kw)
        parsed = extract_json(out2['content'])
        out2['fallback'] = True
        out2['first_finish_reason'] = out.get('finish_reason')
        return parsed, out2
    out['fallback'] = False
    return parsed, out


def chat_json_many(list_of_messages, workers=8, **kw):
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda m: chat_json(m, **kw), list_of_messages))
