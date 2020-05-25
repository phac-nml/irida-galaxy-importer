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


class Sample:

    """A representation of a sample obtained from IRIDA"""

    def __init__(self, name, paired_path, unpaired_path, assembly_path, fast5_path):
        """
        Initialize a sample instance

        :type name: str
        :param name: the name of the sample
        :type paired_path: str
        :param paired_path: the URI to obtain the paired files from the sample
        :type unpaired_path: str
        :param unpaired_path: the URI to get the unpaired files from the sample
        :type assembly_path: str
        :param assembly_path: the URI to get the assembly files from the sample
        :type fast5_path: str
        :param assembly_path: the URI to get fast5 files from the sample
        """

        self.name = name
        self.paired_path = paired_path
        self.unpaired_path = unpaired_path
        self.assembly_path = assembly_path
        self.fast5_path = fast5_path
        self._sample_reads = []  # A list of SampleFile/SamplePair objects

    def __repr__(self):
        num_files = 0
        for item in self.get_files():
            try:
                for _file in item:
                    num_files += 1
            except TypeError:
                num_files += 1

        return_string = self.name + ":\n"
        return_string += "\tPaired path: " + self.paired_path + "\n"
        return_string += "\tSingles path: " + self.unpaired_path + "\n"
        return_string += "\tNumber of files: " + str(num_files) + "\n"
        return return_string

    def add_file(self, new_file):
        self._sample_reads.append(new_file)

    def add_pair(self, pair):
        self.add_file(pair)

    def get_reads(self):
        return self._sample_reads
