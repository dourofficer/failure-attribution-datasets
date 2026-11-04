"""Loader registry. Each loaders/<slug>.py exposes load(limit=None) -> list[record] (see common/schema.py)."""
import importlib

SLUGS = ['who_and_when', 'traceelephant', 'mp_bench', 'who_and_when_pro', 'longrca', 'agentrx', 'symtrace',
         'tracertraj', 'aegis', 'correct_error',
         'mast_data', 'trail',
         'agenterrorbench', 'searchauditbench', 'failure_as_process', 'trajerrbench', 'agenthallu', 'memtrace', 'horizon']


def load(slug, **kw):
    mod = importlib.import_module(f'loaders.{slug}')
    return mod.load(**kw)
