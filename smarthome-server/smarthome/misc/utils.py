import importlib
import sys

if sys.version_info >= (3, 8):
    from typing import TypedDict as TypedDictOriginal
else:
    TypedDictOriginal = dict


class TypedDict(TypedDictOriginal):
    pass


def load_from_string_import(import_path: str):
    """Load a method from a path

    example:

    ```python
    same_method_but_imported_from_str = load_from_string_import("visionlibs.utils.load_from_string_import")
    ```
    """
    import_path = import_path.split(".")  # Split at dots to find module and method
    module = importlib.import_module(".".join(import_path[:-1]))  # Import the module
    func = getattr(module, import_path[-1])  # import the method in the module
    return func
