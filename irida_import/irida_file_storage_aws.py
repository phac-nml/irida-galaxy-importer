#!/usr/bin/env python3
import logging
import boto3

class IridaFileStorageAws:

  def __init__(self, config):
      self.config = config
      self.logger = logging.getLogger('irida_import')
      self.s3 = boto3.resource('s3')
      self.bucket_name = self.config.aws_bucket_name

  def fileExists(file_path):
    """
    Checks to see if aws bucket object exists

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: boolean indicating whether object exists in bucket
    """
    logging.info("Checking if file exists in aws bucket")
    s3Object = s3.Object(bucket_name,filePath)
    #size in bytes
    file_size = s3Object.content_length
    return file_size > 0

  def getFileSize(file_path):
    """
    Gets file size in bytes of object in aws bucket

    :type file_path: str
    :param file_path: the aws bucket 'file path' to the file
    :return: file size in bytes
    """
    logging.info("Getting file size from aws bucket")
    s3Object = s3.Object(bucket_name,file_path)
    #size in bytes
    file_size = s3Object.content_length
    return file_size