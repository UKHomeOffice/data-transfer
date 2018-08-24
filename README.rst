Data Transfer Microservice
==========================

This microservice is a multi-mode file movement wizard. It can transfer files,
at a scheduled interval, between two different storage devices, using different
transfer protocols and storage types.

The application is built for Python 3, but also tested against Python 2.7. It
is **not** compatible with Python 2.6.

**Note**
The application will not work if you have files with spaces in the names and will fail.

**Standard FTP is no longer supported in this app**

Installing and getting started
------------------------------

The application should be installed using ``pip3`` (or ``pip`` for Python 2.7).

To install from a private PyPI server we suggest using ``~/.pypirc`` to configure
your private PyPI connection details::

    pip3 install data-transfer --extra-index-url <Repo-URL>

After installing and setting the configuration settings, the application can be
started with the following command::

    data-transfer


Developing
----------

Start by cloning the project::

    git clone git@github.com:UKHomeOffice/data-transfer.git

Ensure that ``python3`` is installed and on your ``path``.

Installing for local development

These steps will install the application as a local pip installed package,
using symlinks so that any updates you make to the files are automatically
picked up next time you run the application or tests.

Using venv
""""""""""

To install the app using the standard ``python3 venv`` run the following
commands from the project root folder::

    python3 -m venv ~/.virtualenvs/data-transfer
    source ~/.virtualenvs/data-transfer/bin/activate
    pip3 install -e . -r requirements.txt
    export PYTHONPATH=.


Using virtualenvwrapper
"""""""""""""""""""""""

Alternatively, if you are using ``virtualenvwrapper`` then run the following::

    mkvirtualenv data-transfer -p python3
    pip3 install -e . -r requirements.txt
    export PYTHONPATH=.

Dependancies for local testing
""""""""""""""""""""""""""""""

The project's tests require the following dependencies:

* An AWS S3 bucket or a mock
* An FTP server
* An SFTP server

For local development and testing, we suggest running Docker images. The following
will meet the test dependencies and match the default env vars::

    docker run -d --name s3server -p 8000:8000 scality/s3server
    docker run -d --name ftp_server -p 21:21 -p 30000-30009:30000-30009 onekilo79/ftpd_test
    docker run -p 2222:22 -d atmoz/sftp foo:pass:::upload

Test
""""

Once the application is installed and the dependencies are in place, run the
tests::

    pytest tests


Building & publishing
=====================

This project uses ``setuptools`` to build the distributable package.

Remember to update the ``version`` in ``setup.py`` before building the package::

    python setup.py sdist

This will create a ``.tar.gz`` distributable package in ``dist/``. This should be
uploaded to an appropriate PyPI registry.

Deploying
---------

The application should be installed using ``pip3`` (or ``pip`` for Python 2.7).

If installing from a private PyPI server then we suggest using ``~/.pypirc`` to
configure your private PyPI connection details::

    pip3 install data-transfer --extra-index-url <Repo-URL>


Configuration
-------------

The application requires the following environment variables to be set before
running.

All configuration settings automatically default to suitable values for the
tests, based on the local test dependencies running in the Docker images
suggested in this guide.

Application settings
""""""""""""""""""""

These control various application behaviours, where a variable is not required
the default value is used:

+---------------------+----------------------+-----------+-----------------------------------+
|Environment Variable | Example (Default)    | Required  | Description.                      |
+=====================+======================+===========+===================================+
|INGEST_SOURCE_PATH   | /upload/files        | Yes       | Source path                       |
+---------------------+----------------------+-----------+-----------------------------------+
|INGEST_DEST_PATH     | /upload/files/done   | Yes       | Destination path                  |
+---------------------+----------------------+-----------+-----------------------------------+
|MAX_FILES_BATCH      | 5                    | No        | Number to process each run        |
+---------------------+----------------------+-----------+-----------------------------------+
|PROCESS_INTERVAL     | 5                    | No        | Runs the task every (x) seconds.  |
+---------------------+----------------------+-----------+-----------------------------------+
|FOLDER_DATE_OUTPUT   | False                | No        | Moves files to YYYY / MM / DD     |
+---------------------+----------------------+-----------+-----------------------------------+
|TEMP_FOLDER_NAME     | tmp                  | No        | Temp folder name for dual write   |
+---------------------+----------------------+-----------+-----------------------------------+
|LOG_LEVEL            | INFO                 | No        | Log level                         |
+---------------------+----------------------+-----------+-----------------------------------+
|LOG_FILE_NAME        | data-transfer.log    | Yes       | Filename for log output           |
+---------------------+----------------------+-----------+-----------------------------------+
|USE_IAM_CREDS        | False                | Yes       | Indicates to app to use IAM       |
+---------------------+----------------------+-----------+-----------------------------------+
|READ_STORAGE_TYPE    | See footnote         | Yes       | The type of read storage          |
+---------------------+----------------------+-----------+-----------------------------------+
|WRITE_STORAGE_TYPE   | See footnote         | Yes       | The type of write storage         |
+---------------------+----------------------+-----------+-----------------------------------+
|COPY_FILES           | False                | No        | Do not delete from source if true |
+---------------------+----------------------+-----------+-----------------------------------+

Note: the read and write storage types need to be prefixed and options are:

* datatransfer.storage.FolderStorage
* datatransfer.storage.SftpStorage
* datatransfer.storage.S3Storage
* datatransfer.storage.RedisStorage  

* Also ensure that the source and destination paths have the correct leading and
trailing slashes, this will depend on the storage type and the OS. See the
ecosystem.config file for examples.

* When running two or more data-transfer apps to the same target folder, Ensure
you have set the TEMP_FOLDER_NAME variable for each to be different. This stops
any potential race conditions on the moving of the files.


Source / read settings
""""""""""""""""""""""

Provide the connection settings for either sFTP or S3. You only need to
configure the settings associated with the source storage type.

+----------------------------+------------------------+--------------------------+
|Environment Variable        | Example                | Description              |
+============================+========================+==========================+
|READ_FTP_HOST               | localhost              | Hostname or IP of server |
+----------------------------+------------------------+--------------------------+
|READ_FTP_PASSWORD           | pass                   | Password                 |
+----------------------------+------------------------+--------------------------+
|READ_FTP_USER               | user                   | Username                 |
+----------------------------+------------------------+--------------------------+
|READ_FTP_PORT               | 22                     | Port the server uses     |
+----------------------------+------------------------+--------------------------+
|READ_AWS_ACCESS_KEY_ID      | accessKey1             | Access key for S3        |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_BUCKET_NAME     | aws-ingest             | Bucket name              |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_ENCRYPT         | aws:kms                | ServerSideEncryption     |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_HOST            | http://localhost:8000  | URL of S3                |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_REGION          | eu-west-1              | region for s3 bucket     |
+----------------------------+------------------------+--------------------------+
|READ_REDIS_HOST             | localhost              | Hostname or IP of redis  |
+----------------------------+------------------------+--------------------------+
|READ_REDIS_PORT             | 6379                   | Port for redis           |
+----------------------------+------------------------+--------------------------+
|READ_REDIS_PASSWORD*        | pass                   | Password for redis       |
+----------------------------+------------------------+--------------------------+

* If redis password is required

Target / write settings
"""""""""""""""""""""""

Provide the connection settings for either sFTP or S3. You only need to
configure the settings associated with the target storage type.

+----------------------------+-----------------------+-------------------------+
|Environment Variable        | Example               | Description             |
+============================+=======================+=========================+
|WRITE_FTP_HOST              | localhost             | Hostname or IP of server|
+----------------------------+-----------------------+-------------------------+
|WRITE_FTP_USER              | user                  | Username                |
+----------------------------+-----------------------+-------------------------+
|WRITE_FTP_PASSWORD          | pass                  | Password                |
+----------------------------+-----------------------+-------------------------+
|WRITE_FTP_PORT              | 22                    | Port for server         |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_ACCESS_KEY_ID     | accesskey1            | Access key for S3       |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_SECRET_ACCESS_KEY | verysecret            | Secrey key              |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_BUCKET_NAME    | aws-ingest            | Bucket name             |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_ENCRYPT        | aws:kms               | ServerSideEncryption    |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_HOST           | http://localhost:8000 | URL of S3               |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_REGION         | eu-west-1             | region for s3 bucket    |
+----------------------------+-----------------------+-------------------------+
|WRITE_REDIS_HOST            | localhost             | Hostname or IP of redis |
+----------------------------+-----------------------+-------------------------+
|WRITE_REDIS_PORT            | 6379                  | Port for redis          |
+----------------------------+-----------------------+-------------------------+
|WRITE_REDIS_PASSWORD*       | pass                  | Password for redis      |
+----------------------------+-----------------------+-------------------------+


Running the application
-----------------------

To run the application from the command line:

For pip installed versions::

    data-transfer

Calling the application directly::

    python bin/data-transfer

For production use we recommend running the application using PM2, please ensure
that PM2 is installed globally before running this command::

    pm2 start ecosystem.config.js --only data-transfer

Envirnment variables required should be changed in the ecosystem file before
running PM2. It is also recommended to run pm2 from within a python virtual env.

Running Multi-Instances
-----------------------

To run more that one instance of the application with different config settings,
you will need to change/add additional services into the ecosystem config file.

See here for examples:

<http://pm2.keymetrics.io/docs/usage/application-declaration/#process-file>


Windows
-------

The application is portable between linux and windows, however when running the
app on windows there are some specifics you may want to take into account:

1. If you are running the microservice using a batch file or other mechanism
other than PM2, you will need to ensure that the environment variables are
set without quotes.

2. The file paths for FolderStorage should be Windows paths, for FTP,sFTP and
S3 these can be unix format.

For sFTP, and Folder storage ensure paths are absolute without a trailing slash
  /path/to/something

For S3 the path is used with the URL so can be relative, but without a trailing slash
  path/to/something


AWS
---

If you are running the app on a AWS instance that has anIAM policy you can set
the USE_IAM_CREDS var to True and the application will use IAM policies. You must
however ensure that the bucket name is set correctly.


Contributing
""""""""""""

This project is Open source and we welcome ocntributions to and suggestions to
improve the application. Please raise issues in the usual way on Github and for
contributing code:

* Fork the repo github
* Clone the project locally
* Commit your changes to your own branch
* Push your work back to your fork
* Submit a Pull Request so that we can review the changes


Licensing
"""""""""

This application is released under the `BSD license`_.

.. _BSD license: LICENSE.txt
