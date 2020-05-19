#!/usr/bin/env python3
import logging
import os

class IridaFileStorageLocal:

  def fileExists(file_path):
    """
    Checks to see if file exists

    :type file_path: str
    :param file_path: the local path to the file
    :return: boolean indicating whether file exists at path
    """
    logging.info("Checking if file exists on local drive")
    return os.path.isfile(file_path)

  def getFileSize(filePath):
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