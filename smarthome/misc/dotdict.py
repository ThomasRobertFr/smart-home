class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def create_dot_dict(dic):
    for k, v in dic.items():
        if type(v) == dict:
            dic[k] = create_dot_dict(v)
    return DotDict(dic)
