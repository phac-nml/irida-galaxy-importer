import logging
import boto3
from irida_import.import_temp_file import ImportTempFile

class IridaFileStorageAws:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import_aws')
      self.s3 = boto3.resource('s3')
      self.bucket_name = self.config.AWS_BUCKET_NAME

  def fileExists(self, file_path):
    """
    Checks to see if aws bucket object exists. As there
    is no exists function for boto3 we get the s3 object
    content length and if it's greater than 0 then the
    object exists

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: boolean indicating whether object exists in bucket
    """
    aws_blob_path = self.getFilePath(file_path)

    logging.info("Checking if file {0} exists in aws bucket", aws_blob_path)
    try:
      #size in bytes
      file_size = self.getFileSize(file_path)
    except:
      logging.error("File not found in s3 bucket: {0}", aws_blob_path)
      return False
    return file_size > 0

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of object in aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file size in bytes
    """
    aws_blob_path = self.getFilePath(file_path)
    file_size = 0
    logging.info("Getting size of file {0} from aws bucket", aws_blob_path)
    try:
      s3Object = self.s3.Object(self.bucket_name, aws_blob_path)
      #size in bytes
      file_size = s3Object.content_length
    except:
      logging.error("Could not get size of file {0} as it was not found in s3 bucket", aws_blob_path)
    return file_size

  def getFileContents(self, file_path):
    """
    Gets file as string from aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file contents as a string
    """
    aws_blob_path = self.getFilePath(file_path)
    logging.info("Getting contents of file {0} from s3 bucket...", aws_blob_path)
    try:
      s3Object = self.s3.Object(self.bucket_name, aws_blob_path)

      try:
          temp_dir = tempfile.mkdtemp(suffix=None, prefix="aws-import-", dir=None)
          logging.info("Created temporary directory is:", temp_dir)
          temp = tempfile.NamedTemporaryFile(mode='w+t', delete=False, dir=temp_dir)
          logging.info("Created temporary file is:", temp.name)
          temp.write(s3Object.get()["Body"].read())
      finally:
          logging.info("Closing the temporary file")
          temp.close()
      return ImportTempFile(temp.name, temp_dir)
    except:
      logging.error("File {0} was not found in s3 bucket", aws_blob_path)
    return ImportTempFile("", "")

  def getFilePath(self, file_path):
    """
    Gets the correct file_path for the file (preceding / removed)

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file path with the preceding slash removed if it exists
    """
    if file_path[0:1] == "/":
      return file_path[1:]
    return file_path