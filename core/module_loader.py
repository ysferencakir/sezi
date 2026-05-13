import importlib
import inspect
import pkgutil
from pathlib import Path

from loguru import logger

import modules as modules_pkg
from core.base_module import BaseModule
from core import scheduler as sched


def _discover_module_classes() -> list[type[BaseModule]]:
    """Walk the modules/ package and collect every BaseModule subclass."""
    found: list[type[BaseModule]] = []
    pkg_path = Path(modules_pkg.__file__).parent

    for _, mod_name, is_pkg in pkgutil.iter_modules([str(pkg_path)]):
        full_name = f"modules.{mod_name}"
        try:
            mod = importlib.import_module(full_name)
        except Exception as exc:
            logger.error(f"Failed to import {full_name}: {exc}")
            continue

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(obj, BaseModule)
                and obj is not BaseModule
                and obj.__module__ == full_name
            ):
                found.append(obj)

    return found


_registry: dict[str, BaseModule] = {}


def load_all() -> dict[str, BaseModule]:
    """Instantiate all discovered modules and register their schedules."""
    global _registry
    classes = _discover_module_classes()

    for cls in classes:
        instance = cls()
        if not instance.name:
            logger.warning(f"{cls.__name__} has no 'name', skipping")
            continue
        _registry[instance.name] = instance
        sched.register_module(instance)
        logger.info(f"Loaded module: {instance.name}")

    return _registry


def get(name: str) -> BaseModule | None:
    return _registry.get(name)


def all_modules() -> list[BaseModule]:
    return list(_registry.values())
