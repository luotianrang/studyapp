from ..core.logger import get_logger

logger = get_logger(__name__)


def save_deepseek_config(secrets_file: str, api_key: str, model: str) -> dict:
    logger.warning("DeepSeek config is deprecated and ignored")
    raise ValueError("DeepSeek 配置已停用，系统现已改为本地自动分析。")
