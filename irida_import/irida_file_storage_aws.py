import logging
import tempfile
import shutil
import boto3

from irida_import.import_temp_file import ImportTempFile

class IridaFileStorageAws:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import_aws')
      self.s3 = boto3.client('s3', aws_access_key_id=self.config.AWS_ACCESS_KEY, aws_secret_access_key=self.config.AWS_SECRET_KEY)
      self.bucket_name = self.config.AWS_BUCKET_NAME

  def file_exists(self, file_path):
    """
    Checks to see if aws bucket object exists. As there
    is no exists function for boto3 we get the s3 object
    content length and if it's greater than 0 then the
    object exists

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: boolean indicating whether object exists in bucket
    """

    aws_blob_path = self.get_file_path(file_path)

    try:
      logging.info("Checking if file {0} exists in aws bucket", aws_blob_path)

      #size in bytes
      file_size = self.get_file_size(file_path)
    except:
      logging.error("File not found in s3 bucket: {0}", aws_blob_path)
      return False
    return file_size > 0

  def get_file_size(self, file_path):
    """
    Gets file size in bytes of object in aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file size in bytes
    """

    aws_blob_path = self.get_file_path(file_path)
    file_size = 0

    try:
      logging.info("Getting size of file {0} from aws bucket", aws_blob_path)
      s3Object = self.s3.Object(self.bucket_name, aws_blob_path)

      #size in bytes
      file_size = s3Object.content_length
    except:
      logging.error("Could not get size of file {0} as it was not found in s3 bucket", aws_blob_path)
    return file_size

  def get_file_contents(self, file_path):
    """
    Gets file as string from aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file contents as a string
    """

    aws_blob_path = self.get_file_path(file_path)

    try:
      logging.info("Getting contents of file {0} from s3 bucket", aws_blob_path)
      # Gets the s3Object from aws bucket
      s3Object = self.s3.Object(self.bucket_name, aws_blob_path)

      try:
          # Create a temp directory and temp file
          temp_dir = tempfile.mkdtemp(suffix=None, prefix="aws-import-", dir=None)
          logging.info("Created temporary directory is:", temp_dir)
          temp = tempfile.NamedTemporaryFile(mode='w+t', delete=False, dir=temp_dir)
          logging.info("Created temporary file is:", temp.name)

          # Write s3Object contents to temp file
          temp.write(s3Object.get()["Body"].read())
      finally:
          logging.info("Closing the temporary file")
          temp.close()
      return ImportTempFile(temp.name, temp_dir)
    except:
      logging.error("Unable to get contents of file {0} as it was not found in the aws bucket", aws_blob_path)
    return ImportTempFile("", "")

  def get_file_path(self, file_path):
    """
    Gets the correct file_path for the file (preceding / removed)

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file path with the preceding slash removed if it exists
    """

    if file_path[0:1] == "/":
      return file_path[1:]
    return file_path

  def cleanup_temp_downloaded_files(self, import_temp_file):
    """
    Cleanup the temporary file download from aws and it's temporary directory
    :type import_temp_file: obj
    :param import_temp_file: The ImportTempFile object containing the directory and file paths
    """

    try:
      # Remove the temp directory and contents
      shutil.rmtree(import_temp_file.dir_path)
    except:
      logging.error("Unable to get cleanup temporary directory {0} and it's contents", import_temp_file.dir_path)
