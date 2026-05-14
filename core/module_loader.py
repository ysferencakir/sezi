from typing import Type
from loguru import logger
from core.base_module import BaseModule
from core.scheduler import register_module


_modules: dict[str, BaseModule] = {}


def load_all() -> None:
    """Dynamically load all BaseModule subclasses from modules/ directory."""
    try:
        from modules.health import HealthModule
        register(HealthModule())
        logger.info("Modules loaded successfully")
    except ImportError as e:
        logger.error(f"Failed to load modules: {e}")


def register(module: BaseModule) -> None:
    """Register a module instance and schedule its jobs."""
    _modules[module.name] = module
    register_module(module)
    logger.info(f"Registered module: {module.name}")


def get(name: str) -> BaseModule | None:
    """Get module by name."""
    return _modules.get(name)


def all_modules() -> list[BaseModule]:
    """Get all registered modules."""
    return list(_modules.values())
