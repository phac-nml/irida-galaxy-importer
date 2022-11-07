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

class ImportTempFile:

    """A representation of a temporary file obtained from an object store"""

    def __init__(self, file_path, dir_path):
        """
        Create a import temp file instance.

        :type file_path: str
        :param file_path: the path to the temp file
        :type dir_path: str
        :param dir_path: the path to the temp file directory
        """

        self.file_path = file_path
        self.dir_path = dir_path

    def __eq__(self, import_temp_file):
        equal = False

        try:
            if self.file_path == import_temp_file.file_path and self.dir_path == import_temp_file.dir_path:
                equal = True
        except AttributeError:
            pass

        return equal

    def __repr__(self):
        return self.file_path + " @ " + self.dir_path
