"""Thin OpenAI-compatible client for the local vLLM server with a sqlite response cache.

Usage:
    from common.llm import LLM
    llm = LLM()                       # qwen3.8-27b on localhost:8210
    out = llm.chat([{"role":"user","content":"..."}], max_tokens=2000, thinking=False)
    out["text"], out["reasoning"], out["usage"], out["cached"]
    outs = llm.chat_many(list_of_message_lists, workers=8, ...)   # threaded, order preserved
Every call is cached on (model, messages, params); set cache=False to bypass.
"""
import hashlib, json, os, sqlite3, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DB = os.path.join(os.path.dirname(HERE), "cache", "llm_cache.sqlite")


class LLM:
    def __init__(self, base_url="http://localhost:8210/v1", model="qwen3.8-27b", cache_db=CACHE_DB, timeout=3600):
        self.base_url, self.model, self.timeout = base_url, model, timeout
        os.makedirs(os.path.dirname(cache_db), exist_ok=True)
        self._db = sqlite3.connect(cache_db, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, ts REAL)")
        self._db.commit()
        self._lock = threading.Lock()

    def _key(self, messages, params):
        return hashlib.sha256(json.dumps([self.model, messages, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def _get(self, key):
        with self._lock:
            row = self._db.execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _put(self, key, value):
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO cache VALUES (?,?,?)", (key, json.dumps(value, ensure_ascii=False), time.time()))
            self._db.commit()

    def chat(self, messages, max_tokens=4096, temperature=0.0, thinking=False, cache=True, tag=None, retries=3, **extra):
        params = {"max_tokens": max_tokens, "temperature": temperature, "thinking": thinking, "tag": tag, **extra}
        key = self._key(messages, params)
        if cache:
            hit = self._get(key)
            if hit is not None:
                hit["cached"] = True
                return hit
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature,
                "chat_template_kwargs": {"enable_thinking": bool(thinking)}}
        for k, v in extra.items():
            body[k] = v
        req = urllib.request.Request(self.base_url + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        last = None
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    resp = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                last = e.read().decode()[:2000]
                if e.code == 400:  # context too long etc.: do not retry
                    out = {"text": None, "reasoning": None, "usage": None, "error": last, "cached": False}
                    if cache:
                        self._put(key, out)
                    return out
                time.sleep(2 * (attempt + 1))
            except Exception as e:  # noqa
                last = repr(e)
                time.sleep(2 * (attempt + 1))
        else:
            return {"text": None, "reasoning": None, "usage": None, "error": last, "cached": False}
        ch = resp["choices"][0]
        msg = ch["message"]
        out = {"text": msg.get("content"), "reasoning": msg.get("reasoning_content") or msg.get("reasoning"),
               "usage": resp.get("usage"), "finish_reason": ch.get("finish_reason"), "error": None, "cached": False}
        if cache:
            self._put(key, out)
        return out

    def chat_many(self, list_of_messages, workers=8, **kw):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(lambda m: self.chat(m, **kw), list_of_messages))

    def count_tokens(self, text):
        """Rough token count via the server tokenizer endpoint (falls back to chars/3.5)."""
        try:
            req = urllib.request.Request(self.base_url.replace("/v1", "") + "/tokenize",
                                         data=json.dumps({"model": self.model, "prompt": text}).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())["count"]
        except Exception:
            return int(len(text) / 3.5)


if __name__ == "__main__":
    llm = LLM()
    t0 = time.time()
    o = llm.chat([{"role": "user", "content": "Reply with the single word OK."}], max_tokens=20, cache=False)
    print(o, round(time.time() - t0, 2), "s")
    o = llm.chat([{"role": "user", "content": "What is 17*23? Think briefly."}], max_tokens=800, thinking=True, cache=False)
    print("thinking:", (o["reasoning"] or "")[:200].replace("\n", " "), "| text:", (o["text"] or "")[:100])
    print("tokens in 10k chars:", llm.count_tokens("word " * 2000))
