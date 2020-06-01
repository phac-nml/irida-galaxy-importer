import logging
from azure.storage.blob import baseblobservice

class IridaFileStorageAzure:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')
      self.container_name = self.config.AZURE_CONTAINER_NAME
      self.blob_service = baseblobservice.BaseBlobService(account_name=self.config.AZURE_ACCOUNT_NAME, account_key=self.config.AZURE_ACCOUNT_KEY)

  def fileExists(self, file_path):
    """
    Checks to see if azure blob exists

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: boolean indicating whether blob exists
    """
    logging.info("Checking if file exists in azure blob")
    blob_exists = self.blob_service.exists(self.container_name, file_path[1:])
    return blob_exists

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of azure blob

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: file size in bytes
    """
    logging.info("Getting file size from azure blob")
    blob = self.blob_service.get_blob_properties(self.container_name, file_path[1:])
    #size in bytes
    size = blob.properties.content_length
    return size

  def getFileContents(self, file_path):
    logging.info("Getting file contents from azure blob")
    blob_item= self.blob_service.get_blob_to_text(self.container_name, file_path[1:])
    return blob_item.content