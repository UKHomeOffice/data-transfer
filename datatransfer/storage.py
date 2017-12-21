"""Storage module"""

import errno
import ftplib
from ftplib import FTP
import logging
import os
import stat
import tempfile
import boto3
import botocore
import paramiko


LOGGER = logging.getLogger(__name__)


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


    def list_dir(self):
        """Lists the contents of the directory.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the directory.

        """
        try:
            return [file for file in os.listdir(self.path) if
                    os.path.isfile(os.path.join(self.path, file))]
        except OSError:
            LOGGER.error('Error trying to read path ' + self.path)
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            with open(os.path.join(self.path, file_name), 'rb') as file:
                return file.read()
        except OSError:
            LOGGER.error(
                'Error trying to read file ' + os.path.join(self.path, file_name))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            with open(os.path.join(self.path, file_name), 'wb+') as file:
                file.write(content)

            return True
        except OSError:
            LOGGER.error('Error trying to write file '
                         + os.path.join(self.path, file_name))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            os.remove(os.path.join(self.path, file_name))
            return True
        except OSError as err:
            if err.errno == errno.ENOENT:
                LOGGER.warning('File for deletion was not found '
                               + os.path.join(self.path, file_name))
            else:
                LOGGER.error('Error trying to delete file '
                             + os.path.join(self.path, file_name))
                raise
        except:
            LOGGER.exception('Unexpected error')
            raise

class FtpStorage:
    """Abstraction for using an FTP server for storage.

    Can list the contents of the FTP server and supports read, write and delete
    operations on the FTP server.

    As part of initialising the storage it checks whether the desired storage
    path exists, if it doesn't exist then the required directories are created.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide the `path` and FTP server connection details.

    """
    def __init__(self, conf):
        self.path = conf.get('path')
        self.ftp = FTP(conf.get('FTP_HOST'))
        self.ftp.login(conf.get('FTP_USER'), conf.get('FTP_PASSWORD'))
        self.check_dir_path(self.path.split('/'))

    def check_dir_exists(self, folder):
        """Checks whether a specific directory exists on the FTP server.

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
        directory_list = []
        found = False
        try:
            self.ftp.retrlines('LIST', directory_list.append)
            for file in directory_list:
                if file.split()[-1] == folder and file.lower().startswith('d'):
                    self.ftp.cwd(folder)
                    found = True

            return found
        except ftplib.all_errors as err:
            LOGGER.error('Error checking ftp directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
                self.ftp.mkd(next_level)
                self.ftp.cwd(next_level)

            self.check_dir_path(directory)

    def list_dir(self):
        """Lists the contents of the FTP server.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the FTP server.

        """
        try:
            self.ftp.cwd(self.path)
            return self.ftp.nlst()
        except ftplib.all_errors as err:
            LOGGER.error('Error listing ftp directory contents' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

    def read_file(self, file_name):
        """Reads a specific file from the FTP server.

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
        try:
            self.ftp.cwd(self.path)
            with tempfile.NamedTemporaryFile('w+b') as temp_file:
                self.ftp.retrbinary(
                    'RETR ' + file_name,
                    temp_file.write
                )
                return temp_file.read()
        except ftplib.all_errors as err:
            LOGGER.error('Error reading file from ftp server '
                         + os.path.join(self.path, file_name)  + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

    def write_file(self, file_name, content):
        """Writes content to a file to the FTP server.

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
        try:
            self.ftp.cwd(self.path)
            with tempfile.NamedTemporaryFile('w+b') as file_obj:
                file_obj.write(content)
                self.ftp.storbinary('STOR ' + file_name, file_obj)
            return True
        except ftplib.all_errors as err:
            LOGGER.error('Error writing file to ftp server '
                         + os.path.join(self.path, file_name)  + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

    def delete_file(self, file_name):
        """Deletes a file from the FTP server.

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
        try:
            self.ftp.cwd(self.path)
            self.ftp.delete(file_name)
            return True
        except ftplib.all_errors as err:
            LOGGER.error('Error deleting file from ftp server '
                         + os.path.join(self.path, file_name)  + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

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
        self.path = conf.get('path')
        sftp_client = self.get_sftp_client(conf)
        self.sftp = sftp_client
        self.check_dir_path(self.path.split('/'))


    @staticmethod
    def get_sftp_client(conf):
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
        return paramiko.SFTPClient.from_transport(transport)

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
        found = False
        try:
            for file in self.sftp.listdir_attr():
                if str(file).split()[-1] == folder and stat.S_ISDIR(file.st_mode):
                    self.sftp.chdir(folder)
                    found = True

            return found
        except IOError as err:
            LOGGER.error('Error checking ftp directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
            LOGGER.error('Error listing sftp directory contents' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            self.sftp.chdir(self.path)
            with tempfile.NamedTemporaryFile('w+b') as temp_file:
                self.sftp.getfo(file_name, temp_file)
                return temp_file.read()
        except IOError as err:
            if err.errno == errno.ENOENT:
                LOGGER.warning('File not found when reading sFTP '
                               + os.path.join(self.path, file_name))
            else:
                LOGGER.error('Error reading file from sftp server '
                             + os.path.join(self.path, file_name) + str(err))
                raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            self.sftp.chdir(self.path)
            with self.sftp.open(file_name, 'w+b') as file_obj:
                file_obj.write(content)
            return True
        except IOError as err:
            if err.errno == errno.ENOENT:
                LOGGER.error('(File not found) Check the path is not relative '
                             + os.path.join(self.path, file_name))
                raise
            else:
                LOGGER.error('Error writing file to sftp server '
                             + os.path.join(self.path, file_name)  + str(err))
                raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            self.sftp.chdir(self.path)
            self.sftp.remove(file_name)
            return True
        except IOError as err:
            LOGGER.error('Error deleting file from ftp server '
                         + os.path.join(self.path, file_name)  + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

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
    resource = boto3.resource(
        's3',
        endpoint_url=conf.get('AWS_S3_HOST'),
        aws_access_key_id=conf.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=conf.get('AWS_SECRET_ACCESS_KEY')
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
    if bucket_name not in [bucket.name for bucket in s3resource.buckets.all()]:
        return s3resource.create_bucket(Bucket=bucket_name)
    return s3resource.Bucket(bucket_name)

class S3Storage:
    """Abstraction for using an S3 bucket for storage.

    Can list the contents of the S3 bucket and supports read, write and delete
    operations on the S3 bucket.

    Parameters
    ----------
    conf : dict of `str`: `str`
        Used to provide the `path` and S3 bucket connection details.

    """
    def __init__(self, conf):
        self.path = conf.get('path')
        self.bucket = get_bucket(conf.get('AWS_S3_BUCKET_NAME'), conf)

    def list_dir(self):
        """Lists the contents of the S3 bucket.

        Returns
        -------
        :obj:`list` of `str`
            A list of all files in the S3 bucket.

        """
        try:
            return [o.key for o in self.bucket.objects.filter(Prefix=self.path)]
        except botocore.exceptions.ClientError as err:
            LOGGER.error('Error listing S3 directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            with tempfile.NamedTemporaryFile('w+b') as temp_file:
                self.bucket.download_file(file_name, temp_file.name)
                with open(temp_file.name) as data:
                    return data.read()
        except botocore.exceptions.ClientError as err:
            LOGGER.error('Error listing S3 directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
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
        try:
            with tempfile.NamedTemporaryFile('w+b') as file_obj:
                file_obj.write(content)
                self.bucket.upload_fileobj(file_obj, self.path + file_name)
            return True
        except botocore.exceptions.ClientError as err:
            LOGGER.error('Error listing S3 directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise

    def delete_file(self, file_name):
        """Deletes a file from the S3 bucket.

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
        try:
            self.bucket.delete_objects(
                Delete={
                    'Objects': [{
                        'Key': file_name,
                    }],
                    'Quiet': True
                }
            )
            return True
        except botocore.exceptions.ClientError as err:
            LOGGER.error('Error listing S3 directory ' + str(err))
            raise
        except:
            LOGGER.exception('Unexpected error')
            raise
