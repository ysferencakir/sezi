import uvicorn
from loguru import logger

from core.config import settings

if __name__ == "__main__":
    logger.info(f"Starting Sezi [{settings.app_env}]")
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_dev,
        log_level=settings.log_level.lower(),
    )
