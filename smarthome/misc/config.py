import itertools
import os

import pkg_resources
import yaml
import pipes

from smarthome.misc.dotdict import DotDictWithNone


# Merge data structures
def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        d = dict(a)
        d.update({k: merge(a.get(k, None), b[k]) for k in b})
        return d

    if isinstance(a, list) and isinstance(b, list):
        return [merge(x, y) for x, y in itertools.zip_longest(a, b)]

    return a if b is None else b


# Read config file, keep env
def read_file_keep_env(filename):
    f = open(filename, "r")
    out = ""
    for line in f:
        if "#env" in line:
            out += line + "\n"
    return out


def data_to_env(data, prefix):
    env = ""
    for k, v in data.items():
        if type(v) == dict:
            env += data_to_env(v, prefix + k + "_")
        else:
            k = pipes.quote(prefix + k)
            v = pipes.quote(str(v))
            env += "%s=%s\n" % (k, v)
    return env


# Convert YAML config to .env file
def export_to_env():
    config = get_dict()
    env_file = data_to_env(config, "")
    open(".env", "w").write(env_file)


# return config
def get_dict():
    config_priv = {}
    config_path = pkg_resources.resource_filename("smarthome", "data/config.yml")
    config_priv_path = pkg_resources.resource_filename("smarthome", "data/config-private.yml")

    config = yaml.load(open(config_path, "r"), Loader=yaml.FullLoader)
    if os.path.isfile(config_priv_path):
        config_priv = yaml.load(open(config_priv_path, "r"), Loader=yaml.FullLoader)
    return merge(config, config_priv)


# return config
def get():
    return DotDictWithNone(get_dict())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "env":
        export_to_env()
