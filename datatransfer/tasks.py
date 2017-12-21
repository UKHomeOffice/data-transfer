"""Tasks module"""

import logging

from datatransfer import settings
from datatransfer import storage #This is required
from datatransfer import utils

LOGGER = logging.getLogger(__name__)


READSTORAGETYPE = utils.my_import(settings.READ_STORAGE_TYPE)
WRITESTORAGETYPE = utils.my_import(settings.WRITE_STORAGE_TYPE)


def storage_type(path, read_write):
    """Sets up the storage conf values.

    When setting the storage type the abstract class requires the configuration
    values for the source and destination.

    Parameters
    ----------
    path : dict of `str`: `str`
        Used to provide the `path` and S3 bucket connection details.

    read_write: 'str'
        Used to indicate to the function if the storage

    Returns
    -------

    obj:

    Returns the class object for the type of storage that was set in the
    configuration.

    """
    if read_write == 'r':
        if ((settings.READ_STORAGE_TYPE.endswith('FtpStorage')) or
                (settings.READ_STORAGE_TYPE.endswith('sFtpStorage'))):
            conf = {
                'path': path,
                'FTP_HOST': settings.READ_FTP_HOST,
                'FTP_USER': settings.READ_FTP_USER,
                'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
                'FTP_PORT': settings.READ_FTP_PORT
            }
            LOGGER.info('Setting read storage to FTP')
            return READSTORAGETYPE(conf)
        elif settings.READ_STORAGE_TYPE.endswith('S3Storage'):
            conf = {
                'path': path,
                'AWS_S3_HOST': settings.READ_AWS_S3_HOST,
                'AWS_S3_BUCKET_NAME': settings.READ_AWS_S3_BUCKET_NAME,
                'AWS_ACCESS_KEY_ID': settings.READ_AWS_ACCESS_KEY_ID,
                'AWS_SECRET_ACCESS_KEY': settings.READ_AWS_SECRET_ACCESS_KEY
            }
            LOGGER.info('Setting read storage to S3')
            return READSTORAGETYPE(conf)
        elif settings.READ_STORAGE_TYPE.endswith('FolderStorage'):
            conf = {
                'path': path
            }
            LOGGER.info('Setting read storage to File server')
            return READSTORAGETYPE(conf)
    elif read_write == 'w':
        if ((settings.WRITE_STORAGE_TYPE.endswith('FtpStorage')) or
                (settings.WRITE_STORAGE_TYPE.endswith('SftpStorage'))):
            conf = {
                'path': path,
                'FTP_HOST': settings.WRITE_FTP_HOST,
                'FTP_USER': settings.WRITE_FTP_USER,
                'FTP_PASSWORD': settings.WRITE_FTP_PASSWORD,
                'FTP_PORT': settings.WRITE_FTP_PORT
            }
            LOGGER.info('Setting write storage to FTP/sFTP')
            return WRITESTORAGETYPE(conf)
        elif settings.WRITE_STORAGE_TYPE.endswith('S3Storage'):
            conf = {
                'path': path,
                'AWS_S3_HOST': settings.WRITE_AWS_S3_HOST,
                'AWS_S3_BUCKET_NAME': settings.WRITE_AWS_S3_BUCKET_NAME,
                'AWS_ACCESS_KEY_ID': settings.WRITE_AWS_ACCESS_KEY_ID,
                'AWS_SECRET_ACCESS_KEY': settings.WRITE_AWS_SECRET_ACCESS_KEY
            }
            LOGGER.info('Setting write storage to S3')
            return WRITESTORAGETYPE(conf)
        elif settings.WRITE_STORAGE_TYPE.endswith('FolderStorage'):
            conf = {
                'path': path
            }
            LOGGER.info('Setting write storage to File server')
            return WRITESTORAGETYPE(conf)


def process_files():
    """Processes the files found at the source storage.

    This task can be run to move the files from the source path to the new path.
    It is called by the main schedule process and uses the config values to
    determine the files to process.

    Parameters
    ----------
    none

    """
    LOGGER.info('Started processing files')
    try:
        read_storage = storage_type(settings.SOURCE_PATH, 'r')
        write_storage = storage_type(settings.DEST_PATH, 'w')
    except Exception as err:
        LOGGER.exception('Error with storage: %s', err)
        raise
    files = read_storage.list_dir()[:settings.MAX_FILES_BATCH]
    for file_name in files:
        try:
            data = read_storage.read_file(file_name)
            write_storage.write_file(file_name, data)
            read_storage.delete_file(file_name)
        except Exception as err:
            LOGGER.exception('Error with file read/write: %s', err)
            raise
