"""Registry of all loader modules (experiments/loaders/<slug>.py).  `load(slug, **kw)` imports the module lazily."""
import importlib
import os
import sys

SLUGS = [
    "who_and_when", "traceelephant", "mp_bench", "who_and_when_pro", "longrca", "agentrx", "symtrace", "tracertraj",
    "aegis", "correct_error", "mast_data", "trail", "agenterrorbench", "searchauditbench", "trajerrbench", "agenthallu",
    "horizon", "memtrace", "failure_as_process",
]
_HERE = os.path.dirname(os.path.abspath(__file__))


def module(slug):
    """Import experiments.loaders.<slug> (falls back to importing <slug> from this directory under -I)."""
    if slug not in SLUGS:
        raise KeyError(f"unknown loader slug {slug!r}; known: {SLUGS}")
    try:
        return importlib.import_module(f"experiments.loaders.{slug}")
    except ImportError:
        if _HERE not in sys.path:
            sys.path.insert(0, _HERE)
        return importlib.import_module(slug)


def load(slug, **kw):
    """Iterate the trajectories of one dataset: load('memtrace', limit=10, subset='mem0')."""
    return module(slug).load(**kw)


def available():
    return [s for s in SLUGS if os.path.exists(os.path.join(_HERE, s + ".py"))]
