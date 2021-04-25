import copy


class DotDict(dict):
    """This class is similar to the common EasyDict, meaning it allows to read / write dict keys
    using mydict.key instead of mydict["key"], making the code slightly clearer.

    We use this instead of EastDict mostly for the `get_dict`, `flatten`, `unflatten` methods that
    do not exist in EasyDict.
    """

    def __init__(self, dic: dict):
        super().__init__(dic)
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = self.__class__(v)  # useful to access the correct class if inherited

    def get_dict(self, deepcopy_values=False) -> dict:
        """Returns a pure dict instead of our class, e.g. for clear YAML dump."""
        out = {}
        for k, v in self.items():
            if isinstance(v, DotDict):
                out[k] = v.get_dict()
            else:
                if deepcopy_values:
                    out[k] = copy.deepcopy(v)
                else:
                    out[k] = v
        return out

    @classmethod
    def unflatten(cls, flatdict: dict):
        """Changes a flat dict with keys like `a.b.c` into a multilevel dict:
        `DotDict.unflatten({"a.b.c.": "val"}) == DotDict({"a": {"b": {"c": "val"}}})`
        """
        out = cls(flatdict)  # useful to access the correct class if inherited
        keys_to_further_unflatten = set()

        for key in list(out.keys()):
            if "." in key:
                ind = key.find(".")
                key_left = key[:ind]
                key_right = key[ind + 1:]

                if out.get(key_left) is None:
                    out[key_left] = {}
                keys_to_further_unflatten.add(key_left)
                out[key_left][key_right] = out.pop(key)

        for key in keys_to_further_unflatten:
            out[key] = cls.unflatten(out[key])

        return out

    def flatten(self) -> dict:
        """Inverse of `unflatten`, changes the multi-level dict into a flat dict:
        `DotDict({"a": {"b": {"c": "val"}}}).flatten() == {"a.b.c.": "val"}`
        """
        out = {}
        for k, v in self.items():
            if isinstance(v, DotDict):
                v = v.flatten()
                for k2, v2 in v.items():
                    out[k + "." + k2] = v2
            else:
                out[k] = v
        return out

    def __copy__(self):
        return self.__class__({k: v for k, v in self.items()})

    def __deepcopy__(self, memodict={}):
        return self.__class__(self.get_dict(deepcopy_values=True))

    # Make using attributes (x.key) behave as using items (x[key])
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class DotDictWithNone(DotDict):
    __getattr__ = dict.get  # Use the get method, which returns not if the key does not exist
