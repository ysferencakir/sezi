import importlib
import inspect
import pkgutil

from loguru import logger

import modules
from core.base_module import BaseModule
from core.scheduler import register_module


_modules: dict[str, BaseModule] = {}


def load_all() -> None:
    """Dynamically discover and register every BaseModule subclass under modules/."""
    for _, subpackage_name, is_pkg in pkgutil.iter_modules(modules.__path__):
        if not is_pkg:
            continue
        try:
            submodule = importlib.import_module(f"modules.{subpackage_name}")
        except ImportError as e:
            logger.error(f"Failed to import modules.{subpackage_name}: {e}")
            continue

        for _, obj in inspect.getmembers(submodule, inspect.isclass):
            if obj is BaseModule or not issubclass(obj, BaseModule):
                continue
            if inspect.isabstract(obj):
                continue
            register(obj())

    logger.info(f"Modules loaded successfully ({len(_modules)} module(s))")


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
