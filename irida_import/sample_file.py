class SampleFile:

    """A representation of a sample file obtained from IRIDA"""

    def __init__(self, path):
        """
        Create a sample file instance.

        :type path: str
        :param path: the URI of the sample file
        """

        self.path = path
        last_slash = path.rfind('/')

        # e.g. from 'http://irida.corefacility.ca/.../sampleFile1'
        # get 'SampleFile1'
        # In the future this can/will change
        self.name = path[last_slash+1:]
