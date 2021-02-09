from __future__ import absolute_import

import logging
from irida_import.import_temp_file import ImportTempFile
from azure.storage.blob import baseblobservice
import tempfile

class IridaFileStorageAzure:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import_azure')
      self.container_name = self.config.AZURE_CONTAINER_NAME

      self.blob_service = baseblobservice.BaseBlobService(
        account_name=self.config.AZURE_ACCOUNT_NAME,
        sas_token=self.config.AZURE_SAS_TOKEN,
        endpoint_suffix=self.config.AZURE_ACCOUNT_ENDPOINT
      )

  def fileExists(self, file_path):
    """
    Checks to see if azure blob exists

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: boolean indicating whether blob exists
    """
    azure_blob_path = self.getFilePath(file_path)
    logging.info("Checking if file {0} exists in azure container...", azure_blob_path)
    blob_exists = self.blob_service.exists(self.container_name, azure_blob_path)
    return blob_exists

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of azure blob

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: file size in bytes
    """
    azure_blob_path = self.getFilePath(file_path)
    size = 0

    try:
      logging.info("Getting size for file {0} from azure container...", azure_blob_path)
      blob = self.blob_service.get_blob_properties(self.container_name, azure_blob_path)
      #size in bytes
      size = blob.properties.content_length
    except:
      logging.error("Could not get file size as file {0} was not found in azure container", azure_blob_path)
    return size

  def getFileContents(self, file_path):
    """
    Gets file as text from azure container

    :type file_path: str
    :param file_path: the azure container 'file path' to the file
    :return: file contents as a text
    """
    azure_blob_path = self.getFilePath(file_path)

    try:
      logging.info("Getting contents of file {0} from azure container...", azure_blob_path)
      # Gets the blob from azure container
      blob_item = self.blob_service.get_blob_to_text(self.container_name, azure_blob_path)

      try:
          temp_dir = tempfile.mkdtemp(suffix=None, prefix="azure-import-", dir=None)
          logging.info("Created temporary directory is:", temp_dir)
          temp = tempfile.NamedTemporaryFile(mode='w+t', delete=False, dir=temp_dir)
          logging.info("Created temporary file is:", temp.name)
          temp.write(blob_item.content)
      finally:
          logging.info("Closing the temporary file")
          temp.close()
      return ImportTempFile(temp.name, temp_dir)
    except:
      logging.error("Unable to get contents of file {0} as it was not found in the azure container", azure_blob_path)
    return ImportTempFile("", "")

  def getFilePath(self, file_path):
    """
    Gets the correct file_path for the file (preceding / removed)

    :type file_path: str
    :param file_path: the azure container 'file path' to the file
    :return: file path with the preceding slash removed if it exists
    """
    if file_path[0:1] == "/":
      return file_path[1:]
    return file_path