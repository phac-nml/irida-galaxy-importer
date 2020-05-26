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


class SamplePair:

    """A representation of a sample pair obtained from IRIDA"""

    def __init__(self, name, forward, reverse):
        """
        Create a sample file instance.

        :type name: str
        :param name: the name of the sample file
        :type path: str
        :param path: the URI of the sample file
        """

        self.forward = forward
        self.reverse = reverse
        self.name = name

    def __repr__(self):
        return self.name + ": \npair -" + str(self.files)
