import logging
import os

class IridaFileStorageLocal:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')

  def fileExists(self, file_path):
    """
    Checks to see if file exists

    :type file_path: str
    :param file_path: the local path to the file
    :return: boolean indicating whether file exists at path
    """
    logging.info("Checking if file exists on local drive")
    return os.path.isfile(file_path)

  def getFileSize(self, file_path):
    """
    Gets file size in bytes of local file

    :type file_path: str
    :param file_path: the local path to the file
    :return: file size in bytes
    """
    logging.info("Getting file size from local drive")
    #size in bytes
    size = os.path.getsize(file_path)
    return size