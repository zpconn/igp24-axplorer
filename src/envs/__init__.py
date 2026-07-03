from src.envs.cycle import SquareEnvironment
from src.envs.igp24 import IGP24Environment
from src.envs.isosceles import IsoscelesEnvironment
from src.envs.sphere import SphereEnvironment

ENVS = {"square": SquareEnvironment, "isosceles": IsoscelesEnvironment, "sphere": SphereEnvironment, "igp24": IGP24Environment}


def build_env(params):
    """
    Build environment.
    """
    env = ENVS[params.env_name](params)
    return env
