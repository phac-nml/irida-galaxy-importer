#!/usr/bin/env python3
import logging
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

class IridaFileStorageAzure:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')
      self.connect_str = config.azure_account_connection_string
      self.container_name = config.azure_container_name
      self.blob_service_client = BlobServiceClient.from_connection_string(self.connect_str)

  def fileExists(file_path):
    """
    Checks to see if azure blob exists

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: boolean indicating whether blob exists
    """
    logging.info("Checking if file exists in azure blob")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_path)
    #size in bytes
    size = blob_client.get_blob_properties().size()
    return size > 0

  def getFileSize(file_path):
    """
    Gets file size in bytes of azure blob

    :type file_path: str
    :param file_path: the azure 'file path' to the file
    :return: file size in bytes
    """
    logging.info("Getting file size from azure blob")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_path)
    #size in bytes
    size = blob_client.get_blob_properties().size()
    return size