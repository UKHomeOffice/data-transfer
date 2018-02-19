module.exports = {
  /**
   * Application configuration
   * Note: not all enviornment variables are required and you can set just the
   * the env vars required for the storage type. Please note the ones below are
   * an example and should be changed before running. Refer to the readme.rst
   * for a full list of configuration variables.
   *
   */
  apps : [

    // First instance of microservice
    {
      name      : "data-transfer",
      script    : "bin/data-transfer",
      interpreter: "python",
      env: {
        INGEST_DEST_PATH : "/upload/files",
        INGEST_SOURCE_PATH : "./tests/files",
        WRITE_STORAGE_TYPE : "datatransfer.storage.SftpStorage",
        READ_STORAGE_TYPE : "datatransfer.storage.FolderStorage",
        LOG_FILE_NAME : "data-transfer-app.log",
        PROCESS_INTERVAL : 4,
        MAX_FILES_BATCH : 25,
        FOLDER_DATE_OUTPUT : "False",
        LOG_LEVEL : "INFO",
        WRITE_FTP_USER : "foo",
        WRITE_FTP_PASSWORD : "pass",
        WRITE_FTP_HOST : "sftp_server",
        WRITE_FTP_PORT : 2222,
      }
    },
    {
      //Second instance of microservice
      name      : "data-transfer-sftp",
      script    : "bin/data-transfer",
      interpreter: "python",
      env: {
        INGEST_DEST_PATH : "upload/files",
        INGEST_SOURCE_PATH : "/upload/files",
        WRITE_STORAGE_TYPE : "datatransfer.storage.S3Storage",
        READ_STORAGE_TYPE : "datatransfer.storage.SftpStorage",
        LOG_FILE_NAME : "data-transfer-app-sftp.log",
        PROCESS_INTERVAL : 8,
        MAX_FILES_BATCH : 25,
        FOLDER_DATE_OUTPUT : "False",
        LOG_LEVEL : "INFO",
        USE_IAM_CREDS : "False",
        READ_FTP_PASSWORD : "pass",
        READ_FTP_PORT : 2222,
        READ_FTP_HOST : "sftp_server",
        READ_FTP_USER : "foo",
        WRITE_AWS_SECRET_ACCESS_KEY : "verySecretKey1",
        WRITE_AWS_S3_BUCKET_NAME : "aws-ingest",
        WRITE_AWS_ACCESS_KEY_ID : "accessKey1",
        WRITE_AWS_S3_HOST : "http://s3server:8000",
        WRITE_AWS_S3_REGION: "eu-west-2",
      }
    },
    {
      //Third instance of microservice
      name      : "data-transfer-S3",
      script    : "bin/data-transfer",
      interpreter: "python",
      env: {
        INGEST_DEST_PATH : "./tests/files",
        INGEST_SOURCE_PATH : "upload/files",
        WRITE_STORAGE_TYPE : "datatransfer.storage.FolderStorage",
        READ_STORAGE_TYPE : "datatransfer.storage.S3Storage",
        LOG_FILE_NAME : "data-transfer-app-s3.log",
        PROCESS_INTERVAL : 10,
        MAX_FILES_BATCH : 25,
        FOLDER_DATE_OUTPUT : "INFO",
        LOG_LEVEL : "DEBUG",
        USE_IAM_CREDS : "False",
        READ_AWS_SECRET_ACCESS_KEY : "verySecretKey1",
        READ_AWS_S3_BUCKET_NAME : "aws-ingest",
        READ_AWS_ACCESS_KEY_ID : "accessKey1",
        READ_AWS_S3_HOST : "http://s3server:8000",
        READ_AWS_S3_REGION: "eu-west-2",
      }
    },
  ]
}
