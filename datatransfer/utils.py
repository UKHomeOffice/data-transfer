"""Utility module"""
from datetime import datetime

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


def get_date_based_folder():
    """Function to return the folder path based on todays date.

    Parameters
    ----------
    None

    Returns
    -------
    str: `str`
        A string that contains the current date YYYY/MM/DD

    """
    folder_date = datetime.utcnow().date().strftime("%Y%/%m%/%d")
    return folder_date


def check_new_day(folder_date):
    """Function that checks what the current date is and determines if a new
    folder is required to be made"""
    return datetime.utcnow().date() != folder_date
