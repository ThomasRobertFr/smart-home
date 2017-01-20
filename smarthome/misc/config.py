import yaml
import pipes
import itertools
from . import dotdict


# Merge data structures
def merge(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        d = dict(a)
        d.update({k: merge(a.get(k, None), b[k]) for k in b})
        return d

    if isinstance(a, list) and isinstance(b, list):
        return [merge(x, y) for x, y in itertools.izip_longest(a, b)]

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

    # Load config files
    # config = yaml.load(read_file_keep_env("config.yml"))
    # config_priv = yaml.load(read_file_keep_env("config-private.yml"))
    # config = merge({}, merge(config, config_priv))
    config = getDict()
    envFile = data_to_env(config, "")
    open(".env", "w").write(envFile)


# return config
def getDict():
    config = yaml.load(open("config.yml", "r"))
    config_priv = yaml.load(open("config-private.yml", "r"))

    return merge({}, merge(config, config_priv))


# return config
def get():
    return dotdict.create_dot_dict(getDict())


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "env":
        export_to_env()
