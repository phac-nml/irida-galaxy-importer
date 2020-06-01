import logging
import boto3

class IridaFileStorageAws:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')
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
    logging.info("Checking if file exists in aws bucket")
    try:
      #size in bytes
      file_size = self.getFileSize(file_path)
    except:
      logging.error("File not found in s3 bucket: {0}", self.getFilePath(file_path))
      return False
    return file_size > 0

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of object in aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file size in bytes
    """
    file_size = 0
    logging.info("Getting file size from aws bucket")
    try:
      s3Object = self.s3.Object(self.bucket_name, self.getFilePath(file_path))
      #size in bytes
      file_size = s3Object.content_length
    except:
      logging.error("Could not get file size as file was not found in s3 bucket: {0}", self.getFilePath(file_path))
    return file_size

  def getFileContents(self, file_path):
    """
    Gets file as string from aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file contents as a string
    """
    logging.info("Getting file contents from s3 bucket...")
    try:
      s3Object = self.s3.Object(self.bucket_name, self.getFilePath(file_path))
      s3ObjectContents = s3Object.get()["Body"].read()
    except:
      logging.error("File not found in s3 bucket: {0}", self.getFilePath(file_path))
    return s3ObjectContents

  def getFilePath(self, file_path):
    """
    Gets the correct file_path for the file (preceding / removed)

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file path with the preceding slash removed if it exists
    """
    if file_path[0:1] == "/"
      return file_path[1:]
    return file_path