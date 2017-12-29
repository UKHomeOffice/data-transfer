import os
from pathlib import Path
import shutil
import unittest
from datetime import datetime, timedelta

from datatransfer import settings
from datatransfer.storage import FolderStorage
from datatransfer.storage import FtpStorage
from datatransfer.storage import S3Storage
from datatransfer.storage import SftpStorage
from datatransfer.tasks import process_files
from datatransfer import utils


# Create your tests here.
TEST_FILE_LIST = ['test_csv.csv', 'test_json.json', 'test_xml.xml']

class TestStorage(unittest.TestCase):
    """ Test class for storage """
    def setup(self):
        """Setup test files"""
        directory = './tests/files/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        for file_name in TEST_FILE_LIST:
            Path(os.path.join(directory, file_name)).touch()

    def test_file_path_listing(self):
        """Check file list works"""
        conf = {
            'path': './tests/files'
        }
        self.setup()
        storage = FolderStorage(conf)
        result = storage.list_dir()
        self.assertListEqual(sorted(result), sorted(TEST_FILE_LIST))
        for file_name in result:
            storage.read_file(file_name)
        self.teardown()

    def test_read_delete_from_s3_bucket(self):
        """Tests the read and delete from the S3 bucket"""
        conf = {
            'path': 'tests/files/done/',
            'AWS_S3_HOST': settings.WRITE_AWS_S3_HOST,
            'AWS_S3_BUCKET_NAME': settings.WRITE_AWS_S3_BUCKET_NAME,
            'AWS_ACCESS_KEY_ID': settings.WRITE_AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': settings.WRITE_AWS_SECRET_ACCESS_KEY
        }
        s3_test_file_list = [conf.get('path') + 'test_csv.csv',
                             conf.get('path') + 'test_json.json',
                             conf.get('path') + 'test_xml.xml']
        storage = S3Storage(conf)
        result = storage.list_dir()
        self.assertListEqual(sorted(result), sorted(s3_test_file_list))
        storage.delete_file(s3_test_file_list[0])
        result = storage.list_dir()
        s3_test_file_list.pop(0)
        self.assertListEqual(sorted(result), sorted(s3_test_file_list))

    def test_ftp_push(self):
        """Tests the ftp push"""
        conf = {
            'path': '/tests/files/done/',
            'FTP_HOST': 'localhost',
            'FTP_USER': 'test',
            'FTP_PASSWORD': 'test',
            'FTP_PORT': '21'
        }
        self.setup()
        storage = FtpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open(os.path.join('./tests/files/', file_name), 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        self.teardown()

    def test_ftp_read(self):
        """Tests the ftp pull"""
        conf = {
            'path': '/tests/files/done/',
            'FTP_HOST': 'localhost',
            'FTP_USER': 'test',
            'FTP_PASSWORD': 'test',
            'FTP_PORT': '21'
        }
        storage = FtpStorage(conf)
        result = storage.list_dir()
        for file_name in result:
            storage.read_file(file_name)
            storage.delete_file(file_name)

        self.assertListEqual(sorted(result), sorted(TEST_FILE_LIST))
        result = storage.list_dir()
        self.assertEqual(len(result), 0)

    def test_sftp_setup(self):
        """Tests the sftp push"""
        conf = {
            'path': '/upload/tests/files/done/',
            'FTP_HOST': 'localhost',
            'FTP_USER': 'foo',
            'FTP_PASSWORD': 'pass',
            'FTP_PORT': '2222'
        }
        SftpStorage(conf)


    def test_sftp_push(self):
        """Tests the sftp push"""
        conf = {
            'path': '/upload/tests/files',
            'FTP_HOST': 'localhost',
            'FTP_USER': 'foo',
            'FTP_PASSWORD': 'pass',
            'FTP_PORT': '2222'
        }
        self.setup()
        storage = SftpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open(os.path.join('./tests/files/', file_name), 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        self.teardown()

    def test_sftp_getlist_read_delete(self):
        """test the sftp list dir"""
        conf = {
            'path': '/upload/tests/files',
            'FTP_HOST': 'localhost',
            'FTP_USER': 'foo',
            'FTP_PASSWORD': 'pass',
            'FTP_PORT': '2222'
        }

        self.setup()
        storage = SftpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open(os.path.join('./tests/files/', file_name), 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        self.teardown()

        result = storage.list_dir()
        self.assertListEqual(sorted(result), sorted(TEST_FILE_LIST))
        for file_name in result:
            storage.delete_file(file_name)

        result = storage.list_dir()
        self.assertEqual(len(result), 0)

    def test_process_files(self):
        """Test moving of files"""
        conf = {
            'path': './tests/files/done'
        }
        self.setup()
        process_files('tests/files', 'tests/files/done')
        storage = FolderStorage(conf)
        result = storage.list_dir()
        self.assertListEqual(sorted(result), sorted(TEST_FILE_LIST))


    def test_folder_storage_delete(self):
        """" Tests the folder storage delete function last as files are Used
            in other tests """
        conf = {
            'path': 'tests/files'
        }
        self.setup()
        storage = FolderStorage(conf)
        result = storage.list_dir()
        for file_name in result:
            storage.delete_file(file_name)

        result = storage.list_dir()
        self.assertEqual(len(result), 0)


    def test_folder_date_path(self):
        date_folder = utils.get_date_based_folder()
        current_date = datetime.utcnow().strftime("%Y%/%m%/%d")
        self.assertEqual(date_folder,current_date)

    def test_new_day(self):
        self.assertTrue(utils.check_new_day(datetime.utcnow().date() - timedelta(days=1)))
        self.assertFalse(utils.check_new_day(datetime.utcnow().date()))


    def teardown(self):
        """"Teardown: also tests the folder storage delete function"""
        if os.path.isdir('./tests/files/done'):
            shutil.rmtree('./tests/files/done')

        for files in TEST_FILE_LIST:
            os.remove(os.path.join('./tests/files', files))
