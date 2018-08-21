"""Tasks module"""

import logging
import os
from datatransfer import settings
from datatransfer import storage #This is required - ignore linter
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
    LOGGER.debug('Task - Storage type called : ' + path + ' - ' + read_write)
    LOGGER.debug('Task - ReadStorage : ' + settings.READ_STORAGE_TYPE
                 + ' - WriteStorage : ' + settings.WRITE_STORAGE_TYPE)
    if read_write == 'r':
        if (settings.READ_STORAGE_TYPE.endswith('SftpStorage')):
            conf = {
                'path': path,
                'FTP_HOST': settings.READ_FTP_HOST,
                'FTP_USER': settings.READ_FTP_USER,
                'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
                'FTP_PORT': settings.READ_FTP_PORT
            }
            LOGGER.info('Task - Setting read storage to SFTP')
            return READSTORAGETYPE(conf)
        elif settings.READ_STORAGE_TYPE.endswith('S3Storage'):
            conf = {
                'path': path,
                'AWS_S3_HOST': settings.READ_AWS_S3_HOST,
                'AWS_S3_BUCKET_NAME': settings.READ_AWS_S3_BUCKET_NAME,
                'AWS_ACCESS_KEY_ID': settings.READ_AWS_ACCESS_KEY_ID,
                'AWS_SECRET_ACCESS_KEY': settings.READ_AWS_SECRET_ACCESS_KEY,
                'AWS_S3_ENCRYPT': settings.READ_AWS_S3_ENCRYPT,
                'AWS_S3_REGION': settings.READ_AWS_S3_REGION,
                'USE_IAM_CREDS': settings.USE_IAM_CREDS,
            }
            LOGGER.info('Task - Setting read storage to S3')
            return READSTORAGETYPE(conf)
        elif settings.READ_STORAGE_TYPE.endswith('FolderStorage'):
            conf = {
                'path': path
            }
            LOGGER.info('Task - Setting read storage to File server')
            return READSTORAGETYPE(conf)
    elif read_write == 'w':
        if (settings.WRITE_STORAGE_TYPE.endswith('SftpStorage')):
            conf = {
                'path': path,
                'FTP_HOST': settings.WRITE_FTP_HOST,
                'FTP_USER': settings.WRITE_FTP_USER,
                'FTP_PASSWORD': settings.WRITE_FTP_PASSWORD,
                'FTP_PORT': settings.WRITE_FTP_PORT
            }
            LOGGER.info('Task - Setting write storage to sFTP')
            return WRITESTORAGETYPE(conf)
        elif settings.WRITE_STORAGE_TYPE.endswith('S3Storage'):
            conf = {
                'path': path,
                'AWS_S3_HOST': settings.WRITE_AWS_S3_HOST,
                'AWS_S3_BUCKET_NAME': settings.WRITE_AWS_S3_BUCKET_NAME,
                'AWS_ACCESS_KEY_ID': settings.WRITE_AWS_ACCESS_KEY_ID,
                'AWS_SECRET_ACCESS_KEY': settings.WRITE_AWS_SECRET_ACCESS_KEY,
                'AWS_S3_ENCRYPT': settings.WRITE_AWS_S3_ENCRYPT,
                'AWS_S3_REGION': settings.WRITE_AWS_S3_REGION,
                'USE_IAM_CREDS': settings.USE_IAM_CREDS,
            }
            LOGGER.info('Task - Setting write storage to S3')
            return WRITESTORAGETYPE(conf)
        elif settings.WRITE_STORAGE_TYPE.endswith('FolderStorage'):
            conf = {
                'path': path
            }
            LOGGER.info('Task - Setting write storage to File server')
            return WRITESTORAGETYPE(conf)


def process_files(source=settings.INGEST_SOURCE_PATH,
                  dest=settings.INGEST_DEST_PATH,
                  copy_files=settings.COPY_FILES):
    """Processes the files found at the source storage.

    This task can be run to move the files from the source path to the new path.
    It is called by the main schedule process and uses the config values to
    determine the files to process.

    Parameters
    ----------
    source: str
        Provides the source path to process, defaults to environment setting

    dest: str
        Provides the destination path to process, defaults to the environment
        setting.
    """

    LOGGER.info('Main - Started processing files')
    LOGGER.debug('Main - OS identified as ' + os.name)
    LOGGER.debug('Main - Read path var : ' + source)
    LOGGER.debug('Main - Write path var : ' + dest)
    try:
        if os.name == 'nt' and settings.WRITE_STORAGE_TYPE.endswith('FolderStorage'):
            LOGGER.debug('Main - OS Identified as Windows for WriteStorage')
            sep = os.sep
        else:
            sep = '/'

        if settings.FOLDER_DATE_OUTPUT == 'True':
            LOGGER.debug('Task - Folder date output set to ' + settings.FOLDER_DATE_OUTPUT)
            if dest.endswith(sep):
                dest = dest + utils.get_date_based_folder()
            else:
                dest = dest + sep + utils.get_date_based_folder()

        if dest.endswith(sep):
            dest = dest + settings.TMP_FOLDER_NAME
        else:
            dest = dest + sep + settings.TMP_FOLDER_NAME

        read_storage = storage_type(source, 'r')
        write_storage = storage_type(dest, 'w')
    except Exception as err:
        LOGGER.exception('Main - Error with storage ' + repr(err))
        raise

    files = read_storage.list_dir()[:settings.MAX_FILES_BATCH]
    LOGGER.debug('Task - List directory successful')
    for file_name in files:
        LOGGER.debug('PROCESS FILE ' + repr(file_name))
        if file_name == '':
            continue
        try:
            contents = read_storage.read_file(file_name)
            write_storage.write_file(file_name, contents)
            if copy_files.capitalize() == "False":
                read_storage.delete_file(file_name)
            if not settings.WRITE_STORAGE_TYPE.endswith('S3Storage'):
                write_storage.move_files()

        except Exception as err:
            LOGGER.exception('Task - Error with file read/write :' + repr(err))
            raise

    read_storage.exit()
    write_storage.exit()
