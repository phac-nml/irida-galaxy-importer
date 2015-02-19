from setuptools import setup


def readme():
    """Returns the readme file"""
    with open('README.md') as f:
        return f.read()

setup(name='irida_import',
      version='0.1',
      description='Import files from IRIDA into Galaxy',
      url='https://irida.corefacility.ca/gitlab/jthiessen/ \
            import-tool-for-galaxy/tree/angular-json-passthrough',
      author='Joel Thiessen',
      author_email='jthiessen@phac-aspc.gc.ca',
      license='Not known yet',
      packages=['irida_import'],
      install_requires=[
          'bioblend',
          'pytest',
      ],
      zip_safe=False)
