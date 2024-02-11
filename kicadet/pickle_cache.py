import hashlib
import gc
import os
import pickle
import re
import warnings
from functools import cache
from pathlib import Path
from typing import Any, Callable, Optional

CACHE_VERSION = 1

@cache
def get_cache_version() -> int:
    # During development the data structures change all the time and pickled data becomes stale.
    # Use the code modification times as a good-enough "hash" for the code.
    return sum(int(m.stat().st_mtime) for m in Path(__file__).resolve().parent.glob("**/*.py"))

def get_cache_path(path: Path) -> Optional[Path]:
    env_cache_dir = os.environ.get("XDG_CACHE_HOME", None)
    if env_cache_dir:
        cache_dir = Path(env_cache_dir)
    else:
        env_home_dir = os.environ.get("HOME", None)
        if env_home_dir:
            cache_dir = Path(env_home_dir) / ".cache"

    if not cache_dir:
        warnings.warn("You operating system does not seem to specify a cache directory in the standard way")
        return None

    cache_dir = cache_dir / "kicadet"
    cache_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    filename = (
        re.sub(r"[^a-zA-Z0-9_-]", "_", str(path))[:128]
        + "_"
        + hashlib.sha256(str(path).encode("utf-8")).hexdigest()
        + ".kicadet_cache"
    )

    return cache_dir / filename

def load(path: Path | str, loader: Callable[[Path], Any]) -> Any:
    if not isinstance(path, Path):
        path = Path(path)

    cache_path = get_cache_path(path)
    if not cache_path:
        return loader(path)

    header = ("kicadet_cache", get_cache_version(), path.stat().st_mtime)

    try:
        with open(cache_path, "rb") as f:
            up = pickle.Unpickler(f)
            if up.load() != header:
                raise FileNotFoundError()

            gc.disable()
            obj = up.load()

            return obj
    except (FileNotFoundError, PermissionError):
        pass
    finally:
        gc.enable()

    obj = loader(path)
    with open(cache_path, "wb") as f:
        p = pickle.Pickler(f)
        p.dump(header)
        p.dump(obj)

    return obj
