"""
This file is used to kick off the integration tests

it can be used from command line like so:
  $ python3 start_integration_tests.py <branch>
where <branch> is the IRIDA github branch to test against
"""

import sys

import irida_import.tests.integration.tests_integration as tests_integration


def main():
    return tests_integration.start("master")


if __name__ == "__main__":
    sys.exit(main())
