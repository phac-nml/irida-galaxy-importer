"""
Copyright Government of Canada 2015-2020

Written by: National Microbiology Laboratory, Public Health Agency of Canada

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this work except in compliance with the License. You may obtain a copy of the
License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
"""


class SampleFile:

    """A representation of a sample file obtained from IRIDA"""

    def __init__(self, name, path, href, file_size=None, upload_sha_256=None):
        """
        Create a sample file instance.

        :type name: str
        :param name: the name of the sample file
        :type path: str
        :param path: the URI of the sample file
        :type href: str
        :param href: the url of the sample file
        :type file_size: long
        :param file_size: the size of the file in bytes
        :type upload_sha_256: str
        :param upload_sha_256: the hash of the uploaded file
        """

        self.path = path
        self.name = name
        self.href = href
        self.file_size = file_size
        self.upload_sha_256 = upload_sha_256
        self.library_dataset_id = None
        self.verified = False

    def __eq__(self, sample_file):
        equal = False

        try:
            if self.path == sample_file.path:
                equal = True
        except AttributeError:
            pass

        return equal

    def __repr__(self):
        return self.name + " @ " + self.path + " @ " + self.href

    def state(self, gi, library_id):
        return gi.libraries.show_dataset(library_id, self.library_dataset_id)['state']

    def delete(self, gi, library_id):
        return gi.libraries.delete_library_dataset(library_id, self.library_dataset_id, purged=True)['deleted']

    def get_content_type(self):
        content_type_fastq = "application/fastq"
        content_type_fasta = "application/fasta"
        if 'assemblies' in self.href:
            return content_type_fasta
        elif 'fast5' in self.href or 'sequenceFiles' in self.href:
            return content_type_fastq
        else:
            error = ("Unable to detect type of file and set content type. href is:{0}")
            raise ValueError(error)