class Sample:
"""A representation of a sample obtained from IRIDA"""

    def __init__(self, name, path):
        """
        Initialize a sample instance

        :type name: str
        :param name: the name of the sample
        :type path: str
        :param path: the URI to obtain the sample from IRIDA
        """

        self.name = name
        self.path = path
        self.sample_files = []  # A list of SampleFile objects
