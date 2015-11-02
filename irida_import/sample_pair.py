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
