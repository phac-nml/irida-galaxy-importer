import requests
import json

class GalaxyConnector:

    """
    Connect to the Galaxy API directly to perform tasks unsupported by BioBlend

    Methods to allow setting user permissions for a library will be implemented
    here
    """

    def __init__(self, galaxy_url, api_key):
        self.galaxy_url = galaxy_url
        self.api_key = api_key

    def can_modify_lib(self, email, lib_id):
        """
        Check if a user has permission to modify a library

        :type email: str
        :param email: the Galaxy user's email address
        :type lib_id: int
        :param lib_id: the ID of the library to check access for
        """
        url = '/api/libraries/{id}/permissions'.format(id=lib_id)
        params = {}

        response = self.get(url, params)
        resource = response.json()
        print json.dumps(resource, indent=2)
        raise Exception(response.json())



        return True

    def own_lib(self, email, lib_id):
        """
        Give a user ownership of a library

        :type email: str
        :param email: the Galaxy user's email address
        :type lib_id: int
        :param lib_id: the ID of the library to make the user owA
        """

    def get(self, send_url, send_params):
        url = self.galaxy_url + send_url

        payload = send_params.copy()
        payload['key'] = self.api_key

        response = requests.get(url, params = payload)
        return response

