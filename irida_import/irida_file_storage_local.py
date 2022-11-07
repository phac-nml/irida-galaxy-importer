import logging
import os

class IridaFileStorageLocal:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')

  def file_exists(self, file_path):
    """
    Checks to see if file exists

    :type file_path: str
    :param file_path: the local path to the file
    :return: boolean indicating whether file exists at path
    """

    logging.info("Checking if file {0} exists on local drive", file_path)
    return os.path.isfile(file_path)

  def get_file_size(self, file_path):
    """
    Gets file size in bytes of local file

    :type file_path: str
    :param file_path: the local path to the file
    :return: file size in bytes
    """

    logging.info("Getting the size of the file {0} from local drive", file_path)

    #size in bytes
    size = os.path.getsize(file_path)
    return size
