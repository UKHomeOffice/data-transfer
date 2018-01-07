module.exports = {
  /**
   * Application configuration section
   * http://pm2.keymetrics.io/docs/usage/application-declaration/
   */
  apps : [

    // First instance of microservice
    {
      name      : "data-transfer",
      script    : "bin/data-transfer",
      interpreter: "python",
      env: {
        INGEST_DEST_PATH : "tests/files/done",
        INGEST_SOURCE_PATH : "tests/files",
        WRITE_STORAGE_TYPE : "datatransfer.storage.FolderStorage",
        READ_STORAGE_TYPE : "datatransfer.storage.FolderStorage",
        PROCESS_INTERVAL : 5,
        MAX_FILES_BATCH : 5,
        FOLDER_DATE_OUTPUT : "False",
        READ_AWS_SECRET_ACCESS_KEY : "verysecretkey",
        READ_AWS_S3_BUCKET_NAME : "aws-ingest",
        READ_AWS_ACCESS_KEY_ID : "accessKey1",
        READ_AWS_S3_HOST : "http://localhost:8000",
        WRITE_AWS_SECRET_ACCESS_KEY : "verysecretkey",
        WRITE_AWS_S3_BUCKET_NAME : "ws-ingest",
        WRITE_AWS_ACCESS_KEY_ID : "accessKey1",
        WRITE_AWS_S3_HOST : "http://localhost:8000",
        READ_FTP_PASSWORD : "pass",
        READ_FTP_PORT : 21,
        READ_FTP_HOST : "localhost",
        READ_FTP_USER : "user",
        WRITE_FTP_USER : "user",
        WRITE_FTP_PASSWORD : "pass",
        WRITE_FTP_HOST : "localhost",
        WRITE_FTP_PORT : "21",
      }
    },
    {
      //Second instance of microservice
      name      : "data-transfer-ftp",
      script    : "bin/data-transfer",
      interpreter: "python",
      env: {
        INGEST_DEST_PATH : "upload/files/done",
        INGEST_SOURCE_PATH : "upload/files",
        WRITE_STORAGE_TYPE : "datatransfer.storage.FtpStorage",
        READ_STORAGE_TYPE : "datatransfer.storage.FtpStorage",
        PROCESS_INTERVAL : 5,
        MAX_FILES_BATCH : 5,
        FOLDER_DATE_OUTPUT : "False",
        READ_AWS_SECRET_ACCESS_KEY : "verysecretkey",
        READ_AWS_S3_BUCKET_NAME : "aws-ingest",
        READ_AWS_ACCESS_KEY_ID : "accessKey1",
        READ_AWS_S3_HOST : "http://localhost:8000",
        WRITE_AWS_SECRET_ACCESS_KEY : "verysecretkey",
        WRITE_AWS_S3_BUCKET_NAME : "ws-ingest",
        WRITE_AWS_ACCESS_KEY_ID : "accessKey1",
        WRITE_AWS_S3_HOST : "http://localhost:8000",
        READ_FTP_PASSWORD : "pass",
        READ_FTP_PORT : 21,
        READ_FTP_HOST : "localhost",
        READ_FTP_USER : "user",
        WRITE_FTP_USER : "user",
        WRITE_FTP_PASSWORD : "pass",
        WRITE_FTP_HOST : "localhost",
        WRITE_FTP_PORT : "21",
      }
    }
  ]
}
