from __future__ import annotations

import importlib


_ENV_IMPORTS = {
    "square": ("src.envs.cycle", "SquareEnvironment"),
    "isosceles": ("src.envs.isosceles", "IsoscelesEnvironment"),
    "sphere": ("src.envs.sphere", "SphereEnvironment"),
    "igp24": ("src.envs.igp24", "IGP24Environment"),
}


class LazyEnvRegistry(dict):
    def _load(self, key):
        module_name, class_name = _ENV_IMPORTS[key]
        env_class = getattr(importlib.import_module(module_name), class_name)
        self[key] = env_class
        return env_class

    def __getitem__(self, key):
        value = super().__getitem__(key)
        if value is None:
            return self._load(key)
        return value

    def __missing__(self, key):
        return self._load(key)


ENVS = LazyEnvRegistry.fromkeys(_ENV_IMPORTS)


def build_env(params):
    """
    Build environment.
    """
    env = ENVS[params.env_name](params)
    return env
