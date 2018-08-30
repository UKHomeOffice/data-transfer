"""Utility module"""
from datetime import datetime
import json

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
    int_date = str(datetime.utcnow().date())
    return int_date.replace('-', '/')


def check_new_day(folder_date):
    """Function that checks what the current date is and determines if a new
    folder is required to be made"""
    return datetime.utcnow().date() != folder_date

def generate_event(file_name, datetime=datetime):
    """Function to generate json with a timestamp and filname headers.
    """
    return json.dumps({'timestamp': datetime.now().isoformat(),
                'filename': file_name})

def chop_end_of_string(str_input, str_remove):
    """Function that strips the supplied str_remove from the end of the input
    string

    Parameters
    ----------
    str_input: `str`
                A string to be chopped
    str_remove: `str`
                The string to be removed from the end of the input

    Returns
    -------
    str: `str`
        A string that contains the new string

    """
    if str_input.endswith(str_remove):
        return str_input[:-len(str_remove)]
    return str_input
