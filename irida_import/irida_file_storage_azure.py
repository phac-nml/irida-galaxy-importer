from __future__ import absolute_import

import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

class IridaFileStorageAzure:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')
      self.container_name = self.config.AZURE_CONTAINER_NAME
      self.blob_service = BlobServiceClient(
        account_url=self.config.AZURE_ACCOUNT_URL,
        credential=self.config.AZURE_SAS_TOKEN
      )
      self.container_client = self.blob_service.get_container_client(self.container_name)

  def fileExists(self, file_path):
    """
    Checks to see if azure blob exists

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: boolean indicating whether blob exists
    """
    logging.info("Checking if file exists in azure blob...")
    blob_exists = self.container_client.get_blob_client(self.getFilePath(file_path)).exists()
    return blob_exists

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of azure blob

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: file size in bytes
    """
    size = 0
    logging.info("Getting file size from azure blob...")
    try:
      blob = self.container_client.get_blob_client(self.getFilePath(file_path)).get_blob_properties()
      #size in bytes
      size = blob.size
    except:
      logging.error("Could not get file size as file was not found in azure container: {0}", self.getFilePath(file_path))
    return size

  def getFileContents(self, file_path):
    """
    Gets file as text from azure container

    :type file_path: str
    :param file_path: the azure container 'file path' to the file
    :return: file contents as a text
    """
    logging.info("Getting file contents from azure blob...")
    file_contents = ""
    try:
      blob_item = self.container_client.get_blob_client(self.getFilePath(file_path)).download_blob()
      file_contents = blob_item.content_as_text(max_concurrency=1, encoding='UTF-8')
    except:
      logging.error("Unable to get file contents as file was not found in azure container: {0}", self.getFilePath(file_path))
    return file_contents

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