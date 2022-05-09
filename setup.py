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

from setuptools import setup


def readme():
    """Return the readme file"""
    with open('README.md') as f:
        return f.read()

setup(name='irida_import',
      version='2.0.0',
      description='A tool for importing data from IRIDA into Galaxy',
      url='https://github.com/phac-nml/irida-galaxy-importer',
      author='NML Bioinformatics',
      author_email='Bioinfo-Support@phac-aspc.gc.ca',
      license='Apache License, Version 2.0',
      packages=['irida_import'],
      install_requires=[
          'bioblend',
          'oauthlib',
          'requests',
          'requests-oauthlib',
          'simplejson'
      ],
      extras_require={
          "TEST": ["pytest", "pytest-cov", "pytest-mock", "mock", "subprocess32", "selenium", "rauth"],
      },
      zip_safe=False,
      classifiers=[
          'License :: OSI Approved :: Apache Software License',
            'Environment :: Console',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3'
      ])
