Data Transfer Microservice
==========================

This microservice is a multi-mode file movement wizard. It can transfer files,
at a scheduled interval, between two different storage devices, using different
transfer protocols and storage types.

The application is built for Python 3, but also tested against Python 2.7. It
is **not** compatible with Python 2.6.

Installing and getting started
------------------------------

The application should be installed using ``pip3`` (or ``pip`` for Python 2.7).

To install from a private PyPI server we suggest using ``~/.pypirc`` to configure
your private PyPI connection details.

  ``pip3 install data-transfer --extra-index-url <Repo-URL>``

After installing and setting the configuration settings, the application can be
started with the following command:

  ``data-transfer``


Developing
----------

Start by cloning the project:

  ``git clone git@github.com:UKHomeOffice/data-transfer.git``

Ensure that ``python3`` is installed and on your ``path``.

Installing for local development

These steps will install the application as a local pip installed package,
using symlinks so that any updates you make to the files are automatically
picked up next time you run the application or tests.

Using venv
""""""""""

To install the app using the standard ``python3 venv`` run the following
commands from the project root folder:

  ``python3 -m venv ~/.virtualenvs/data-transfer``
  ``source ~/.virtualenvs/data-transfer/bin/activate``
  ``pip3 install -e . -r requirements.txt``


Using virtualenvwrapper
"""""""""""""""""""""""

Alternatively, if you are using ``virtualenvwrapper`` then run the following:

  ``mkvirtualenv data-transfer -p python3``
  ``pip3 install -e . -r requirements.txt``


Dependancies for local testing
""""""""""""""""""""""""""""""

The project's tests require the following dependencies:

- An AWS S3 bucket or a mock
- An FTP server
- An SFTP server

For local development and testing, we suggest running Docker images.

Test
""""

Once the application is installed and the dependencies are in place, run the
tests:

  ``pytest tests``


Building & publishing
=====================

This project uses ``setuptools`` to build the distributable package.

Remember to update the ``version`` in ``setup.py`` before building the package.

  ``python setup.py sdist``

This will create a ``.tar.gz`` distributable package in ``dist/``. This should be
uploaded to an appropriate PyPI registry.

Deploying
---------

The application should be installed using ``pip3`` (or ``pip`` for Python 2.7).

If installing from a private PyPI server then we suggest using ``~/.pypirc`` to
configure your private PyPI connection details.

  ``pip3 install data-transfer --extra-index-url <Repo-URL>``


Configuration
-------------

The application requires the following environment variables to be set before
running.

All configuration settings automatically default to suitable values for the
tests, based on the local test dependencies running in the Docker images
suggested in this guide.

Application settings
""""""""""""""""""""

These control various application behaviour, where a variable is not required
the deafult value is used:

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
|LOG_LEVEL            | INFO                 | No        | Log level                         |
+---------------------+----------------------+-----------+-----------------------------------+
|READ_STORAGE_TYPE    | See footnote         | Yes       | The type of read storage          |
+---------------------+----------------------+-----------+-----------------------------------+
|WRITE_STORAGE_TYPE   | See footnote         | Yes       | The type of write storage         |
+---------------------+----------------------+-----------+-----------------------------------+

Note: the read and write storage types need to be prefixed and options are:

* datatransfer.storage.FolderStorage
* datatransfer.storage.FtpStorage
* datatransfer.storage.SftpStorage
* datatransfer.storage.S3Storage


Source / read settings
""""""""""""""""""""""

Provide the connection settings for either FTP, sFTP or S3. You only need to
configure the settings associated with the source storage type.

+----------------------------+------------------------+--------------------------+
|Environment Variable        | Example                | Description              |
+============================+========================+==========================+
|READ_FTP_HOST               | localhost              | Hostname or IP of server |
+----------------------------+------------------------+--------------------------+
|READ_FTP_PASSWORD           | pass                   | Password                 |
+----------------------------+------------------------+--------------------------+
|READ_FTP_PORT               | 21                     | Port the server uses     |
+----------------------------+------------------------+--------------------------+
|READ_AWS_ACCESS_KEY_ID      | accessKey1             | Access key for S3        |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_BUCKET_NAME     | aws-ingest             | Bucket name              |
+----------------------------+------------------------+--------------------------+
|READ_AWS_S3_HOST            | http://localhost:8000  | URL of S3                |
+----------------------------+------------------------+--------------------------+


Target / write settings
"""""""""""""""""""""""

Provide the connection settings for either FTP, sFTP or S3. You only need to
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
|WRITE_FTP_PORT              | 21                    | Port for server         |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_ACCESS_KEY_ID     | accesskey1            | Access key for S3       |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_SECRET_ACCESS_KEY | verysecret            | Secrey key              |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_BUCKET_NAME    | aws-ingest            | Bucket name             |
+----------------------------+-----------------------+-------------------------+
|WRITE_AWS_S3_HOST           | http://localhost:8000 | URL of S3               |
+----------------------------+-----------------------+-------------------------+


Running the application
-----------------------

To run the application from the command line:

For pip installed versions:

  ``data-transfer``

Calling the application directly:

  ``python bin/data-transfer``

For production use we recommend running the application using PM2, please ensure
that PM2 is installed globally before running this command:

  ``pm2 start ecosystem.config.js --only data-transfer``

Envirnment variables required should be changed in the ecosystem file before
running PM2.

Running Multi-Instances
-----------------------

To run more that one instance of the application with different config settings,
you will need to change/add additional services into the ecosystem config file.

See here for examples:

http://pm2.keymetrics.io/docs/usage/application-declaration/#process-file


Contributing
""""""""""""

This project is Open source and we welcome ocntributions to and suggestions to
improve the application. Please raise issues in the usual way on Github and for
contributing code:

- Fork the repo github
- Clone the project locally
- Commit your changes to your own branch
- Push your work back to your fork
- Submit a Pull Request so that we can review the changes


Licensing
"""""""""

This application is released under the [BSD license](LICENSE.txt).
