#!/usr/bin/env python3
"""Fetch the source logs that MP-Bench annotation files point to.

MP-Bench ships only annotation pointers (log_source URLs).  Two kinds exist:
  * Who&When JSON logs (mingyin1/Agents_Failure_Attribution) -> we already have an
    identical copy from the HF dataset Kevin355/Who_and_When; we fetch them anyway
    from GitHub so the MP-Bench copy is self-contained and can be diffed.
  * MAST console_log.txt (multi-agent-systems-failure-taxonomy/MAST) plus the
    sibling prompt.txt and expected_answer.txt.

Usage: python3 -I mp_bench_fetch_sources.py <mp_bench_raw_dir> <out_dir>
Files are stored under <out_dir>/<sha1(url)[:16]>/... with an index.json map.
Nothing fetched is ever executed.
"""
import glob
import hashlib
import json
import os
import sys
import time
import urllib.request
from urllib.parse import urlparse, unquote


def tree_to_raw(url):
    p = urlparse(url)
    parts = p.path.strip("/").split("/")
    if p.netloc == "github.com" and len(parts) >= 5 and parts[2] == "tree":
        owner, repo, _, branch = parts[:4]
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{'/'.join(parts[4:])}"
    return url


def fetch(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mp-bench-fetch/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed {url}: {last}")


def main():
    raw_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    srcs = {}
    for f in sorted(glob.glob(os.path.join(raw_dir, "MP-Bench", "*", "*", "*.json"))):
        with open(f) as fh:
            d = json.load(fh)
        srcs.setdefault(d["log_source"], []).append(os.path.relpath(f, raw_dir))
    index = {}
    n_ok = n_fail = 0
    for url, refs in sorted(srcs.items()):
        key = hashlib.sha1(url.encode()).hexdigest()[:16]
        d = os.path.join(out_dir, key)
        os.makedirs(d, exist_ok=True)
        raw = tree_to_raw(url)
        base = raw.rsplit("/", 1)[0]
        fname = unquote(raw.rsplit("/", 1)[1])
        entry = {"log_source": url, "raw_url": raw, "refs": refs, "files": {}}
        targets = [(raw, fname)]
        if fname.endswith(".txt"):
            targets += [(f"{base}/prompt.txt", "prompt.txt"), (f"{base}/expected_answer.txt", "expected_answer.txt")]
        for u, name in targets:
            path = os.path.join(d, name)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                entry["files"][name] = "cached"
                continue
            try:
                data = fetch(u)
                with open(path, "wb") as fh:
                    fh.write(data)
                entry["files"][name] = "ok"
            except Exception as e:  # noqa
                entry["files"][name] = f"ERROR {e}"
        ok = entry["files"].get(fname) in ("ok", "cached")
        n_ok += ok
        n_fail += (not ok)
        index[key] = entry
        print(("OK  " if ok else "FAIL"), key, url, flush=True)
    with open(os.path.join(out_dir, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1)
    print(f"done: {n_ok} ok, {n_fail} failed, {len(srcs)} distinct sources")


if __name__ == "__main__":
    main()
