import sys
import os


def panic(message):
    print(message, file=sys.stderr)
    exit(1)


def get_env_int(env_name, default=None):
    try:
        return int(os.environ[env_name])
    except (KeyError, ValueError, TypeError) as exc:
        if isinstance(exc, KeyError) and default is not None:
            return default

        panic(f"Error: {env_name} env variable is not set or has invalid value.")


def get_env(env_name, default=None):
    try:
        return os.environ[env_name]
    except KeyError:
        if default is not None:
            return default
        panic(f"Error: {env_name} env variable is not set.")


def batch(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

