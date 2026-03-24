import os

try:
    from src.utils.configs import load_config
except ImportError:
    import sys

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from utils.configs import load_config


def _get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_retry_queue_settings() -> tuple[int, int]:
    config_path = os.path.join(_get_project_root(), "config", "configs.yaml")
    config = load_config(config_path) or {}
    retry_cfg = config.get("retry_queue", {}) if isinstance(config, dict) else {}

    wait_seconds = int(retry_cfg.get("post_pipeline_wait_seconds", 20))
    max_rows = int(retry_cfg.get("max_rows_per_run", 500))

    if wait_seconds < 0:
        wait_seconds = 0
    if max_rows < 1:
        max_rows = 1

    return wait_seconds, max_rows


def is_429_error(error_value) -> bool:
    if error_value is None:
        return False
    return "429" in str(error_value)

