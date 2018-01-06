"""Settings module - used to import the configuration settings from the
enviornment variables"""

import os
import logging
import logging.config


#  Source paths and locations for storage.
SOURCE_PATH = os.environ.get('INGEST_SOURCE_PATH', 'tests/files')
DEST_PATH = os.environ.get('INGEST_DEST_PATH', 'tests/files/done')

#  Storage types for read and write. I.e Source and Destination
READ_STORAGE_TYPE = os.environ.get('READ_STORAGE_TYPE', 'datatransfer.storage.FolderStorage')
WRITE_STORAGE_TYPE = os.environ.get('WRITE_STORAGE_TYPE', 'datatransfer.storage.FolderStorage')

# Env's for FTP server config. Allows for two configs for read and write.
READ_FTP_HOST = os.environ.get('READ_FTP_HOST', 'localhost')
READ_FTP_USER = os.environ.get('READ_FTP_USER', 'test')
READ_FTP_PASSWORD = os.environ.get('READ_FTP_PASSWORD', 'pass')
READ_FTP_PORT = os.environ.get('READ_FTP_PORT', '22')

WRITE_FTP_HOST = os.environ.get('WRITE_FTP_HOST', 'localhost')
WRITE_FTP_USER = os.environ.get('WRITE_FTP_USER', 'foo')
WRITE_FTP_PASSWORD = os.environ.get('WRITE_FTP_PASSWORD', 'pass')
WRITE_FTP_PORT = os.environ.get('WRITE_FTP_PORT', '2222')

# Envs for S3 bucket
READ_AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'accessKey1')
READ_AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'verySecretKey1')
READ_AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME', 'aws-ingest')
READ_AWS_S3_HOST = os.environ.get('AWS_S3_HOST', 'http://localhost:8000')

WRITE_AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'accessKey1')
WRITE_AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'verySecretKey1')
WRITE_AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME', 'aws-ingest')
WRITE_AWS_S3_HOST = os.environ.get('AWS_S3_HOST', 'http://localhost:8000')

#Max number of files to process at a time.
MAX_FILES_BATCH = int(os.environ.get('MAX_FILES_BATCH', 5))
PROCESS_INTERVAL = int(os.environ.get('PROCESS_INTERVAL', 5))
FOLDER_DATE_OUTPUT = os.environ.get('FOLDER_DATE_OUTPUT', False)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

#  Loggin config
DICTLOGCONFIG = {
    'version': 1,
    'handlers': {
        'fileHandler': {
            'class': 'logging.FileHandler',
            'formatter': 'myFormatter',
            'filename': 'data-transfer-app.log'
        }
    },
    'root':  {
        'handlers':   ['fileHandler'],
        'level': LOG_LEVEL
    },
    'formatters': {
        'myFormatter': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
}

logging.config.dictConfig(DICTLOGCONFIG)
