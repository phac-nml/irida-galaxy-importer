class SampleFile:
    def __init__(self, path):
        self.path = path
        last_slash = path.rfind('/')
        self.name = path[last_slash+1:]
