"""Test module"""
import os
import json
from pathlib import Path
import shutil
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from datatransfer import settings
from datatransfer.storage import FolderStorage
from datatransfer.storage import S3Storage
from datatransfer.storage import SftpStorage
from datatransfer.storage import RedisStorage
from datatransfer.tasks import process_files
from datatransfer import utils


# Create your tests here.
TEST_FILE_LIST = ['test_csv.csv', 'test_json.json', 'test_xml.xml']
TEST_CONTENT = b'THIS SHOULD STILL BE HERE'

class TestStorage(unittest.TestCase):
    """ Test class for storage """
    def setup(self):
        """Setup test files"""
        directory = './tests/files/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        for file_name in TEST_FILE_LIST:
            Path(os.path.join(directory, file_name)).touch()
            with open(os.path.join(directory, file_name),'wb') as test_file:
                test_file.write(TEST_CONTENT)
            test_file.close

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
            'path': 'tests',
            'AWS_S3_HOST': settings.WRITE_AWS_S3_HOST,
            'AWS_S3_BUCKET_NAME': settings.WRITE_AWS_S3_BUCKET_NAME,
            'AWS_ACCESS_KEY_ID': settings.WRITE_AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': settings.WRITE_AWS_SECRET_ACCESS_KEY,
            'AWS_S3_REGION': settings.WRITE_AWS_S3_REGION,
            'USE_IAM_CREDS': settings.USE_IAM_CREDS,
        }
        s3_test_file_list = ['test_csv.csv',
                             'test_json.json',
                             'test_xml.xml']

        storage = S3Storage(conf)
        result = storage.list_dir()
        self.assertListEqual(sorted(result), sorted(s3_test_file_list))
        for file_name in result:
            content = storage.read_file(file_name)
            self.assertEqual(TEST_CONTENT, content)

        storage.delete_file(s3_test_file_list[0])
        result = storage.list_dir()
        s3_test_file_list.pop(0)
        self.assertListEqual(sorted(result), sorted(s3_test_file_list))

    def test_s3_delete_all(self):
        """Teardown for s3 bucket"""
        conf = {
            'path': 'tests',
            'AWS_S3_HOST': settings.WRITE_AWS_S3_HOST,
            'AWS_S3_BUCKET_NAME': settings.WRITE_AWS_S3_BUCKET_NAME,
            'AWS_ACCESS_KEY_ID': settings.WRITE_AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': settings.WRITE_AWS_SECRET_ACCESS_KEY,
            'AWS_S3_REGION': settings.WRITE_AWS_S3_REGION,
            'USE_IAM_CREDS': settings.USE_IAM_CREDS,
        }

        storage = S3Storage(conf)
        result = storage.list_dir()

        for file_name in result:
            storage.delete_file(file_name)

        result = storage.list_dir()
        self.assertEqual(len(result), 0)

    def test_sftp_setup(self):
        """Tests the sftp push"""
        conf = {
            'path': '/upload/tests/files/done/',
            'FTP_HOST': settings.READ_FTP_HOST,
            'FTP_USER': settings.READ_FTP_USER,
            'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
            'FTP_PORT': settings.READ_FTP_PORT
        }
        SftpStorage(conf)


    def test_sftp_push(self):
        """Tests the sftp push"""
        conf = {
            'path': '/upload/tests/files/tmp',
            'FTP_HOST': settings.READ_FTP_HOST,
            'FTP_USER': settings.READ_FTP_USER,
            'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
            'FTP_PORT': settings.READ_FTP_PORT
        }
        self.setup()
        storage = SftpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open('./tests/files/' + file_name, 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        storage.move_files()
        self.teardown()

    def test_sftp_getlist_read_delete(self):
        """test the sftp list dir"""
        conf = {
            'path': '/upload/tests/files',
            'FTP_HOST': settings.READ_FTP_HOST,
            'FTP_USER': settings.READ_FTP_USER,
            'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
            'FTP_PORT': settings.READ_FTP_PORT
        }

        self.setup()
        storage = SftpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open('./tests/files/' + file_name, 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        self.teardown()

        result = storage.list_dir()
        for file_name in result:
            content = storage.read_file(file_name)
            self.assertEqual(TEST_CONTENT, content)
            storage.delete_file(file_name)

        self.assertListEqual(sorted(result), sorted(TEST_FILE_LIST))
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
        """Tests folder date creation"""
        date_folder = utils.get_date_based_folder()
        int_date = str(datetime.utcnow().date())
        current_date = int_date.replace('-', '/')
        self.assertEqual(date_folder, current_date)

    def test_new_day(self):
        """Tests new day check"""
        self.assertTrue(utils.check_new_day(datetime.utcnow().date() - timedelta(days=1)))
        self.assertFalse(utils.check_new_day(datetime.utcnow().date()))

    def test_string_chop(self):
        """Test the string chop method"""
        val = 'test/test/tmp'
        rem = '/test'
        rem2 = '/tmp'
        rem3 = 'tmp'
        result2 = 'test/test'
        result1 = 'test/test/'
        self.assertEqual(utils.chop_end_of_string(val, rem), val)
        self.assertEqual(utils.chop_end_of_string(val, rem2), result2)
        self.assertEqual(utils.chop_end_of_string(val, rem3), result1)

    def test_copy_files_local(self):
        """Tests files are not removed from local source when copying"""
        self.setup()
        conf = {
            'path': 'tests/files'
        }
        process_files('tests/files', 'tests/files/done', "True")
        storage_source = FolderStorage(conf)
        storage_dest = FolderStorage({'path': 'tests/files/done'})
        source = storage_source.list_dir()
        dest = storage_dest.list_dir()
        self.assertEqual(source, dest)
        self.assertNotEqual(len(source), 0)

    def test_generate_event(self):
        mock_datetime = MagicMock()
        now = MagicMock()
        mock_datetime.now.return_value = now
        now.isoformat.return_value = "2018-08-24T17:01:44.827543"
        test_json = json.dumps({"timestamp": "2018-08-24T17:01:44.827543", "filename": "bbb"})
        self.assertEqual(test_json, utils.generate_event("bbb", datetime=mock_datetime))

    def test_move_file_callback(self):
        conf = {
            'path': '/upload/tests/files/tmp',
            'FTP_HOST': settings.READ_FTP_HOST,
            'FTP_USER': settings.READ_FTP_USER,
            'FTP_PASSWORD': settings.READ_FTP_PASSWORD,
            'FTP_PORT': settings.READ_FTP_PORT
        }
        self.setup()
        storage = SftpStorage(conf)
        for file_name in TEST_FILE_LIST:
            with open('./tests/files/' + file_name, 'rb') as tmpfile:
                data = tmpfile.read()
                storage.write_file(file_name, data)
        mock = MagicMock()
        mock.test_func.return_value = True
        storage.move_files(callback=mock.test_func)
        mock.test_func.assert_called()
        self.teardown()

    def teardown(self):
        """"Teardown: also tests the folder storage delete function"""
        if os.path.isdir('./tests/files/done'):
            shutil.rmtree('./tests/files/done')

        for files in TEST_FILE_LIST:
            os.remove(os.path.join('./tests/files', files))
