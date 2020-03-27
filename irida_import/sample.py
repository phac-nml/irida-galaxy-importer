class Sample:

    """A representation of a sample obtained from IRIDA"""

    def __init__(self, name, paired_path, unpaired_path, assembly_path):
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
        """

        self.name = name
        self.paired_path = paired_path
        self.unpaired_path = unpaired_path
        self.assembly_path = assembly_path
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
