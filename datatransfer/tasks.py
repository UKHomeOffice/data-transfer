"""Tasks module"""

import logging
import os
import json
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
        elif settings.READ_STORAGE_TYPE.endswith('RedisStorage'):
            conf = {
                'path': path,
                'host': settings.READ_REDIS_HOST,
                'port': settings.READ_REDIS_PORT,
                'password': settings.READ_REDIS_PASSWORD,
            }
            LOGGER.info('Task - Setting read storage to Redis')
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
        elif settings.WRITE_STORAGE_TYPE.endswith('RedisStorage'):
            conf = {
                'path': path,
                'host': settings.WRITE_REDIS_HOST,
                'port': settings.WRITE_REDIS_PORT,
                'password': settings.WRITE_REDIS_PASSWORD,
            }
            LOGGER.info('Task - Settings write storage to Redis')
        return WRITESTORAGETYPE(conf)

def build_dest_str(dest):
    """Builds destination string with appropriate seperator and
    tmp location, based on the storage type.

    Parameters
    ----------
    dest: str
        The ingest destination path
    """
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
    elif not settings.WRITE_STORAGE_TYPE.endswith('RedisStorage'):
        dest = dest + sep + settings.TMP_FOLDER_NAME
    return dest

def move_file(file_name, source=settings.INGEST_SOURCE_PATH,
                         dest=settings.INGEST_DEST_PATH,
                         copy_files=settings.COPY_FILES):
    """Moves or copies a specified file from the specified source location
    to the specified destination location

    Parameters
    ----------
    file_name: str
        Name of file to be moved
    """
    try:
        dest = build_dest_str(dest)
        read_storage = storage_type(source, 'r')
        write_storage = storage_type(dest, 'w')
    except Exception as err:
        LOGGER.exception('Main - Error with storage ' + repr(err))
        raise
    LOGGER.debug('PROCESS FILE ' + repr(file_name))
    if file_name == '':
        pass
    try:
        contents = read_storage.read_file(file_name)
        write_storage.write_file(file_name, contents)
        if copy_files.capitalize() == "False":
            read_storage.delete_file(file_name)
        if not settings.WRITE_STORAGE_TYPE.endswith(('S3Storage', 'RedisStorage')):
            write_storage.move_files()

    except Exception as err:
        LOGGER.exception('Task - Error with file read/write :' + repr(err))
        raise

def move_file_callback(ch, method, properties, body):
    """Function to be passed as a callback for event consumption.
    Gets filename from mq event, attempts to move file and acks if successful.
    """
    file_name = json.loads(body.decode('utf-8'))["filename"]
    move_file(file_name)
    re_publish = settings.READ_MQ_REPUBLISH_QUEUE
    if re_publish is not None:
        mq = storage.create_mq("read")
        mq.publish_event(file_name, queue_name=re_publish)
        mq.exit()
        LOGGER.debug('MessageQueue - File moved, published to ' + re_publish)
    ch.basic_ack(delivery_tag = method.delivery_tag)


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
        dest = build_dest_str(dest)
        read_storage = storage_type(source, 'r')
        write_storage = storage_type(dest, 'w')
    except Exception as err:
        LOGGER.exception('Main - Error with storage ' + repr(err))
        raise

    if settings.WRITE_MQ.capitalize() == "True":
        LOGGER.info('Main - Publish to MessageQueue: True')
        mq = storage.create_mq("write")
        for file_name in read_storage.list_dir():
            mq.publish_event(file_name)
            LOGGER.debug('Main - Published {0}'.format(file_name))
        mq.exit()
    else:
        if settings.READ_MQ.capitalize() == "True":
            mq = storage.create_mq("read")
            mq.consume(callback=move_file_callback)
        else:
            files = read_storage.list_dir()[:settings.MAX_FILES_BATCH]
            for file_name in files:
                move_file(file_name, copy_files=copy_files)

    read_storage.exit()
    write_storage.exit()
