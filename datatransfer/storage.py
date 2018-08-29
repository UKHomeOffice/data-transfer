"""Storage module"""

import errno
import ftplib
import logging
import shutil
import os
import stat
import tempfile
import boto3
import botocore
import paramiko
import redis
import pika
from datatransfer import settings
from datatransfer import utils

LOGGER = logging.getLogger(__name__)

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

class FolderStorage:
    """Abstraction for using a local directory for storage.

    Can list the contents of the directory and supports read, write and delete
    operations on files within the directory.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide the `path` for the directory.

    """
    def __init__(self, conf):
        self.path = conf.get('path')
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        LOGGER.debug('Folder - Set storage type to Folder')
        LOGGER.debug('Folder - Path: ' + self.path)

    def list_dir(self):
        """Lists the contents of the directory.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the directory.

        """
        LOGGER.debug('Folder - List contents of folder directory')
        try:
            return [file for file in os.listdir(self.path) if
                    os.path.isfile(os.path.join(self.path, file))]
        except OSError:
            LOGGER.error('Folder - Error trying to read path ' + self.path)
            raise
        except Exception as err:
            LOGGER.exception('Folder - Unexpected error ' + repr(err))
            raise

    def read_file(self, file_name):
        """Reads a specific file from the directory.

        Parameters
        ----------
        file_name : str
            Name of the file to read; including the file extension but not the
            file's path.

        Returns
        -------
        str
            A string containing the contents of the file being read.

        """
        LOGGER.debug('Folder - Read file : ' + os.path.join(self.path, file_name))
        try:
            with open(os.path.join(self.path, file_name), 'rb') as file:
                return file.read()
        except OSError:
            LOGGER.error(
                'Folder - Error trying to read file ' + os.path.join(self.path, file_name))
            raise
        except Exception as err:
            LOGGER.exception('Folder - Unexpected error ' + repr(err))
            raise

    def write_file(self, file_name, content):
        """Writes content to a file to the directory.

        Parameters
        ----------
        file_name : str
            Name of the file to write to; including the file extension but not
            the file's path.
        content : str
            The content to be written to the file.

        Returns
        -------
        bool
            Returns True once the file is successfully written.

        """
        LOGGER.debug('Folder - Write to file : ' + os.path.join(self.path, file_name))
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            with open(os.path.join(self.path, file_name), 'w+b') as file:
                file.write(content)

            return True
        except OSError as err:
            LOGGER.error('Folder - Error trying to write file '
                         + os.path.join(self.path, file_name) + ' - ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('Folder - Unexpected error ' + repr(err))
            raise

    def move_files(self, callback=None):
        """Moves content from the tmp location to the target directory.

        Parameters
        ----------
        none

        Returns
        -------
        bool
            Returns True once the files have been moved.

        """
        LOGGER.debug('Folder - Move files : ' + self.path)
        try:
            source = self.path
            dest = utils.chop_end_of_string(source, (os.sep + settings.TMP_FOLDER_NAME))
            files = os.listdir(source)

            for filename in files:
                LOGGER.debug('Folder - Trying to move file : '
                             + os.path.join(self.path, filename) + ' to ' + dest)
                shutil.move(os.path.join(source, filename), os.path.join(dest, filename))
                if callback is not None:
                    callback(filename)

            return True
        except OSError:
            LOGGER.error('Folder - Error trying to move files ' + self.path)
            raise
        except Exception as err:
            LOGGER.exception('Folder - Unexpected error ' + repr(err))
            raise


    def delete_file(self, file_name):
        """Deletes a file from the directory.

        Parameters
        ----------
        file_name : str
            Name of the file to write to; including the file extension but not
            the file's path.

        Returns
        -------
        bool
            Returns True once the file is successfully deleted.

        """
        LOGGER.debug('Folder - Delete file : ' + os.path.join(self.path, file_name))
        try:
            os.remove(os.path.join(self.path, file_name))
            return True
        except OSError as err:
            if err.errno == errno.ENOENT:
                LOGGER.warning('Folder - File for deletion was not found '
                               + os.path.join(self.path, file_name))
            else:
                LOGGER.error('Folder - Error trying to delete file '
                             + os.path.join(self.path, file_name))
                raise
        except Exception as err:
            LOGGER.exception('Folder - Unexpected error ' + repr(err))
            raise

    def exit(self):
        LOGGER.debug('Folder - Exit function')


class SftpStorage:
    """Abstraction for using an sFTP server for storage.

    Can list the contents of the sFTP server and supports read, write and delete
    operations on the sFTP server.

    As part of initialising the storage it checks whether the desired storage
    path exists, if it doesn't exist then the required directories are created.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide the `path` and sFTP server connection details.

    """
    def __init__(self, conf):
        LOGGER.debug('sFTP - Set storage type to Sftp')
        self.path = conf.get('path')
        LOGGER.debug('sFTP - Path: ' + self.path)
        self.sftp_session = self.get_sftp_transport(conf)
        self.sftp = paramiko.SFTPClient.from_transport(self.sftp_session)
        self.check_dir_path(self.path.split('/'))

    @staticmethod
    def get_sftp_transport(conf):
        """Takes the configuration for the sFTP and returns a client connection.

        Creates the connection to the server. It will also look for the local
        ssh keys and use them if they exist.

        Parameters
        ----------
        conf : dict of `str`: `str`
            Used to provide the `path` and FTP server connection details.


        Returns
        -------
        :obj: sftp paramiko client
            Returns a client connection to the sftp server.

        """
        transport = paramiko.Transport((conf.get('FTP_HOST'),
                                        int(conf.get('FTP_PORT'))))
        transport.connect(username=conf.get('FTP_USER'),
                          password=conf.get('FTP_PASSWORD'))
        return transport

    def check_dir_exists(self, folder):
        """Checks whether a specific directory exists on the sFTP server.

        It only searches a specific level in the file system heirarchy. The
        level at which it searches is linked to progress through the loop in
        the `check_dir_path()` function that called it.

        Parameters
        ----------
        folder : str
            Name of the directory that is being checked for.

        Returns
        -------
        bool
            Returns True if the directory exists, False if it doesn't.

        """
        LOGGER.debug('sFTP - Checking directory exists : ' + folder)
        found = False
        try:
            for file in self.sftp.listdir_attr():
                if str(file).split()[-1] == folder and stat.S_ISDIR(file.st_mode):
                    self.sftp.chdir(folder)
                    found = True

            return found
        except IOError as err:
            LOGGER.error('Error checking ftp directory ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def check_dir_path(self, directory):
        """Checks whether the directories in the path exist and if they don't
        it creates them.

        Parameters
        ----------
        directory : :obj:`list` of `str`
            A list containing the elements of the directory path to check.

        """
        if len(directory) > 0:
            next_level = directory.pop(0)
            if next_level != '' and not self.check_dir_exists(next_level):
                self.sftp.mkdir(next_level)
                self.sftp.chdir(next_level)

            self.check_dir_path(directory)

    def list_dir(self):
        """Lists the contents of the sFTP server.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the sFTP server Excludes folders.

        """
        LOGGER.debug('sFTP - List directory ' + self.path)
        file_list = []
        try:
            i = 0
            self.sftp.chdir(self.path)
            for file in self.sftp.listdir_attr():
                if not stat.S_ISDIR(file.st_mode):
                    file_list.append(str(file).split()[-1])
                    i += 1

            return file_list

        except IOError as err:
            LOGGER.error('sFTP - Error listing sftp directory contents' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def read_file(self, file_name):
        """Reads a specific file from the sFTP server.

        Parameters
        ----------
        file_name : str
            Name of the file to read; including the file extension but not the
            file's path.

        Returns
        -------
        str
            A string containing the contents of the file being read.

        """
        LOGGER.debug('sFTP - Read File : ' + self.path + '/' + file_name)
        try:
            self.sftp.chdir(self.path)
            with tempfile.TemporaryFile('w+b') as temp_file:
                self.sftp.getfo(file_name, temp_file)
                temp_file.flush()
                temp_file.seek(0)
                return temp_file.read()

        except IOError as err:
            if err.errno == errno.ENOENT:
                LOGGER.warning('sFTP - File not found when reading sFTP '
                               + self.path + '/' + file_name)
            else:
                LOGGER.error('sFTP - Error reading file from sftp server '
                             + self.path + '/' + file_name + ' ' + repr(err))
                raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def move_files(self, callback=None):
        """Moves content from the tmp location to the target directory.

        Parameters
        ----------
        none

        Returns
        -------
        bool
            Returns True once the files have been moved.

        """
        LOGGER.debug('sFTP - Move files : ' + self.path)
        try:
            source = self.path
            dest = utils.chop_end_of_string(source, '/' + settings.TMP_FOLDER_NAME)
            files = self.list_dir()
            LOGGER.debug('sFTP - Destination folder : ' + dest)
            for filename in files:
                LOGGER.debug('sFTP - Trying to move file '
                             + filename + ' to ' + dest)
                LOGGER.debug('sFTP - Source filename ' + source + '/' + filename
                             + ' Target filename ' + dest + '/' + filename)
                self.sftp.posix_rename(source + '/' + filename, dest + '/'
                                       + filename)
                if callback is not None:
                    callback(filename)

            return True
        except OSError as err:
            LOGGER.error('sFTP - Error trying to move files ' + self.path
                         + ' - ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def write_file(self, file_name, content):
        """Writes content to a file to the sFTP server.

        Parameters
        ----------
        file_name : str
            Name of the file to write to; including the file extension but not
            the file's path.
        content : str
            The content to be written to the file.

        Returns
        -------
        bool
            Returns True once the file is successfully written.

        """
        LOGGER.debug('sFTP - Write File : ' + self.path + '/' + file_name)
        try:
            self.sftp.chdir(self.path)
            with self.sftp.open(self.path + '/' + file_name, 'w+') as file_obj:
                file_obj.write(content)
            return True
        except IOError as err:
            if err.errno == errno.ENOENT:
                LOGGER.error('sFTP - (File not found) Check the path is not relative '
                             + self.path + '/' + file_name)
                raise
            else:
                LOGGER.error('sFTP - Error writing file to sftp server '
                             + self.path + '/' + file_name + ' ' + repr(err))
                raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def delete_file(self, file_name):
        """Deletes a file from the sFTP server.

        Parameters
        ----------
        file_name : str
            Name of the file to write to; including the file extension but not
            the file's path.

        Returns
        -------
        bool
            returns True once the file is successfully deleted.

        """
        LOGGER.debug('sFTP - Delete File : ' + self.path + '/' + file_name)
        try:
            self.sftp.chdir(self.path)
            self.sftp.remove(file_name)
            return True
        except IOError as err:
            LOGGER.error('sFTP - Error deleting file from ftp server '
                         + self.path + '/' + file_name + ' ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('sFTP - Unexpected error ' + repr(err))
            raise

    def exit(self):
        LOGGER.info('sFTP - Exit function')
        self.sftp.close()
        self.sftp_session.close()

def get_s3_resource(conf):
    """Gets an S3 resource service client; used to access S3 buckets.

    As part of creating the client, a new session is created.

    Uses SSL to secure the connection.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide S3 bucket connection details.

    Returns
    -------
    :obj:
        A reference to an S3 service resource, accessible within the current
        session.

    """
    region_name = conf.get('AWS_S3_REGION')
    endpoint_url = conf.get('AWS_S3_HOST')
    aws_access_key_id = conf.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = conf.get('AWS_SECRET_ACCESS_KEY')
    use_iam_creds = conf.get('USE_IAM_CREDS')

    if use_iam_creds == 'True':
        LOGGER.info('S3 - AWS Credentials not supplied - will revert to IAM if available')
        resource = boto3.resource('s3')
    else:
        resource = boto3.resource('s3', region_name=region_name,
                                  endpoint_url=endpoint_url,
                                  aws_access_key_id=aws_access_key_id,
                                  aws_secret_access_key=aws_secret_access_key,
                                 )

    return resource

def get_bucket(bucket_name, conf):
    """Gets an S3 bucket from an S3 service resource.

    If the bucket doesn't already exist, then it is created.

    Uses the resource service client (and session) that is created by
    `get_s3_resource()`.

    Parameters
    ----------
    bucket_name : str
        The name of the S3 bucket to connect to.
    conf : dict of `str`: `str`
        Used to provide S3 bucket connection details.

    Returns
    -------
    :obj:
        A reference to an S3 bucket resource, accessible within the current
        session.

    """
    s3resource = get_s3_resource(conf)
    return s3resource.Bucket(bucket_name)

class S3Storage:
    """Abstraction for using an S3 bucket for storage.

    Can list the contents of the S3 bucket and supports read, write and delete
    operations on the S3 bucket. Note /TMP_FOLDER_NAME is removed from the path as the file
    lock prevention is not required on S3.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide the `path` and S3 bucket connection details.

    """
    def __init__(self, conf):
        LOGGER.debug('S3 - Set storage type to S3 Bucket')
        self.path = utils.chop_end_of_string(conf.get('path'), ('/' + settings.TMP_FOLDER_NAME))
        self.bucket = get_bucket(conf.get('AWS_S3_BUCKET_NAME'), conf)
        LOGGER.debug('S3 - Path: ' + self.path)
        self.transfer_conf = dict()
        if conf.get('AWS_S3_ENCRYPT'):
            self.transfer_conf.update(ServerSideEncryption=conf.get('AWS_S3_ENCRYPT'))

    def list_dir(self):
        """Lists the contents of the S3 bucket.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the S3 bucket.

        """
        LOGGER.debug('S3 - List bucket contents: ' + self.path)
        try:
            file_list = []
            for o in self.bucket.objects.filter(Prefix=self.path):
                file_name = o.key[len(self.path +'/'):]
                if '/' not in file_name and file_name:
                    file_list.append(os.path.basename(o.key))

            return file_list
        except botocore.exceptions.ClientError as err:
            LOGGER.error('S3 - Error listing S3 directory ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('S3 - Unexpected error ' + repr(err))
            raise

    def read_file(self, file_name):
        """Reads a specific file from the S3 bucket.

        Parameters
        ----------
        file_name : str
            Name of the file to read; including the file extension but not the
            file's path.

        Returns
        -------
        str
            A string containing the contents of the file being read.

        """
        LOGGER.debug('S3 - Read File : ' + self.path + '/' + file_name)
        try:
            with tempfile.TemporaryFile() as temp_file:
                self.bucket.download_fileobj(self.path + '/' + file_name, temp_file)
                temp_file.flush()
                temp_file.seek(0)
                return temp_file.read()


        except botocore.exceptions.ClientError as err:
            LOGGER.error('S3 - Error reading S3 file ' + file_name
                         + ' - ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('S3 - Unexpected error ' + repr(err))
            raise

    def write_file(self, file_name, content):
        """Writes content to a file to the S3 bucket.

        Parameters
        ----------
        file_name : str
            Name of the file to write to; including the file extension but not
            the file's path.
        content : str
            The content to be written to the file.

        Returns
        -------
        bool
            Returns True once the file is successfully written.

        """
        LOGGER.debug('S3 - Write File : ' + self.path + '/' + file_name)
        try:
            with tempfile.NamedTemporaryFile('w+b') as file_obj:
                file_obj.write(content)
                file_obj.flush()
                file_obj.seek(0)

                self.bucket.upload_fileobj(file_obj, self.path + '/' + file_name, self.transfer_conf)
                return True

        except botocore.exceptions.ClientError as err:
            LOGGER.error('S3 - Error writing to S3 directory : ' + file_name
                         + ' - ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('S3 - Unexpected error ' + repr(err))
            raise

    def delete_file(self, file_name):
        """Deletes a file from the S3 bucket.

        Parameters
        ----------
        file_name : str
            Name of the file to delete; including the file extension but not
            the file's path.

        Returns
        -------
        bool
            returns True once the file is successfully deleted.

        """
        LOGGER.debug('S3 - Delete File : ' + self.path + '/' + file_name)
        try:
            self.bucket.delete_objects(
                Delete={
                    'Objects': [{
                        'Key': self.path + '/' + file_name,
                    }],
                    'Quiet': True
                }
            )
            return True
        except botocore.exceptions.ClientError as err:
            LOGGER.error('S3 - Error deleting file from S3 directory :' + file_name
                         + ' - ' + repr(err))
            raise
        except Exception as err:
            LOGGER.exception('S3 - Unexpected error ' + repr(err))
            raise

    def exit(self):
        LOGGER.debug('S3 - Exit function')

class RedisStorage:
    """Abstraction for using a redis instance for storing and retrieving filenames
    Used for storing, retrieving and listing filenames from a redis instance.

    Parameters
    ----------
    conf : dict of 'str' : 'str'
      used to provide connection information.
    """
    def __init__(self, conf, redis=redis):
        LOGGER.debug('Redis - Set storage type to redis: ')
        try:
            self.redis = redis.Redis(
                host = conf.get('host'),
                port = conf.get('port'),
                password = conf.get('password'))
        except redis.ConnectionError as err:
            LOGGER.error('Redis - Error connecting to redis server :' + ' - ' + repr(err))
            raise
        except redis.AuthenticationError as err:
            LOGGER.error('Redis - Error authenticating to redis server :' + ' - ' + repr(err))
            raise
        self.path = conf.get('path')
        LOGGER.debug('Redis - Set redis key: ' + self.path)

    def list_dir(self):
        """Lists contents of redis key.

        Returns
        -------
        list: of b'str'
            A list of all the filename for a configured redis key.

        """
        LOGGER.debug('Redis - List redis key contents: ' + self.path)
        try:
            return self.redis.lrange(self.path, 0, -1)
        except Exception as err:
            LOGGER.exception('Redis - Unexpected error ' + repr(err))
            raise

    def write_file(self, file_name, _content):
        """Write a filename to a redis key.

        Parameters
        ----------
        file_name : str
            Name of the file to write; including the file extension but not
            the file's path.

        Returns
        -------
        bool
            returns True once the file is successfully written to redis.

        """
        LOGGER.debug('Redis - Write filename to redis key : ' + file_name)
        if file_name.encode() not in self.list_dir():
            try:
                self.redis.rpush(self.path, file_name)
                return True
            except Exception as err:
                LOGGER.exception('Redis - Unexpected error ' + repr(err))
                raise

    def delete_file(self, file_name):
        """Remove a filename from a redis key.

        Parameters
        ----------
        file_name : str
            Name of the file to remove

        Returns
        -------
        bool
            return True once file is successfully deleted from redis.

        """
        LOGGER.debug('Redis - Deleting filename from redis key : ' + file_name)
        try:
            self.redis.lrem(self.path, file_name)
            return True
        except Exception as err:
            LOGGER.exception('Redis - Unexpected error ' + repr(err))
            raise

    def exit(self):
        LOGGER.debug('Redis - Exit function')


class MessageQueue:
    """Abstraction for MQ interaction.
    MessageQueue will allow for the publishing and consumption of event from a queue.
    Currently MessageQueue only supports RabbitMQ

    Parameters
    ----------
    conf: dict of 'str' : 'str'
        Provides connection details for the message queue.
    """
    def __init__(self, conf, pika=pika):
        LOGGER.debug('MessageQueue - Creating MessageQueue instance')
        try:
            if conf.get('username') is not None:
                mq_credentials = pika.PlainCredentials(conf.get('username'), conf.get('password'))
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=conf.get('host'),
                                                                               port=int(conf.get('port')),
                                                                               credentials=mq_credentials))
            else:
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=conf.get('host'),
                                                                               port=int(conf.get('port'))))
            self._channel = connection.channel()
            self._channel.confirm_delivery()
            LOGGER.debug('MessageQueue - Connection established')
            self.queue_name = conf.get('queue_name')
            self._channel.queue_declare(queue=conf.get('queue_name'), durable=True)
        except Exception as err:
            LOGGER.exception('MessageQueue - Unexpected error ' + repr(err))
            raise

    def channel(self):
        """Getter for _channel

        Returns
        -------
        obj:
            Pika connection channel object for queue interaction
        """
        return self._channel

    def publish_event(self, file_name):
        """Publishes event to message queue.
        Message delivery to the broker is confirmed or delivery is re-attempted
        Parameters
        ----------
        event: str
            An event to be put on a queue.

        Returns
        -------
        bool
            returns True if event successfully published
        """
        event = utils.generate_event(file_name)
        msg_properties = pika.BasicProperties(delivery_mode=2)
        try:
            if not self.channel().basic_publish(exchange='',
                                                routing_key=self.queue_name,
                                                body=event,
                                                properties=msg_properties):
                # nack received, retry,
                LOGGER.warning('MessageQueue - Failed to send message to broker')
                return self.publish_event(file_name)
            else:
                return True
        except Exception as err:
            LOGGER.exception('MessageQueue - Unexpected error publishing event ' + repr(error))
