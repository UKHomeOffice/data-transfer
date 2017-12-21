"""Utility module"""

def my_import(name):
    """Function converts a string based import into a module object, used for
    dynamically importing modules from config.

    Parameters
    ----------
    :str: `str`
        A string name of the module to import

    Returns
    -------
    :obj: `module`
        A module object converted from the string.

    """
    components = name.split('.')
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
