import boto
from boto.s3.key import Key
from moto import mock_s3
import boto3
import unittest
import pytest

class TestIridaFileStorageAws(unittest.TestCase):
  mock_s3 = mock_s3()

  @pytest.fixture(scope='session')
  def setup_env():
      os.environ['AWS_ACCESS_KEY_ID'] = 'foo'
      os.environ['AWS_SECRET_ACCESS_KEY'] = 'bar'
      os.environ.pop('AWS_PROFILE', None)

  def setUp(self):
      self.mock_s3.start()
      self.location = "eu-west-1"
      self.bucket_name = 'my_aws_bucket'
      self.key_name = 'path/to/newfile.fasta'
      self.key_contents = ">gi|217332573|gb|CP001175.1| Listeria monocytogenes HCC23, complete genome \
                            TTTATTTGAAAGGCTTTGCTGCCGCTTTAGCTCAGTTGGTAGAGCACTTCCATGGTAAGGAAGGGGTCGT"
      s3 = boto.connect_s3()
      bucket = s3.create_bucket(self.bucket_name, location=self.location)
      k = Key(bucket)
      k.key = self.key_name
      k.set_contents_from_string(self.key_contents)

  def tearDown(self):
      self.mock_s3.stop()

  def test_s3_boto3(self):
      s3 = boto3.resource('s3', region_name=self.location)
      bucket = s3.Bucket(self.bucket_name)
      assert bucket.name == self.bucket_name
      # file exists
      keys = list(bucket.objects.filter(Prefix=self.key_name))
      assert len(keys) == 1
      assert keys[0].key == self.key_name
      # gets file size
      size = keys[0].size()
      assert size > 0
      # get file contents
      contents = keys[0].get_contents_as_string()
      assert contents == self.key_contents