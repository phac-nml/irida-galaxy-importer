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

    def __init__(self, name, path):
        """
        Create a sample file instance.

        :type name: str
        :param name: the name of the sample file
        :type path: str
        :param path: the URI of the sample file
        """

        self.path = path
        self.name = name
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
        return self.name + " @ " + self.path

    def state(self, gi, library_id):
        return gi.libraries.show_dataset(library_id, self.library_dataset_id)['state']

    def delete(self, gi, library_id):
        return gi.libraries.delete_library_dataset(library_id, self.library_dataset_id, purged=True)['deleted']
