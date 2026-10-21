import functools
from datetime import datetime
from pathlib import Path


def _write_log(path, action: str, status: str, msg: str = "") -> None:
    if not path:
        return
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {action} | {status} | {msg}\n")
    except OSError:
        # Логирование не должно ронять бизнес-логику
        pass


def log_action(func):
    """Пишет в лог факт вызова метода сервиса и его результат."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0] if args else None
        log_path = getattr(instance, "log_path", None)
        try:
            result = func(*args, **kwargs)
            _write_log(log_path, func.__name__, "OK")
            return result
        except Exception as e:
            _write_log(log_path, func.__name__, "ERROR", f"{type(e).__name__}: {e}")
            raise

    return wrapper