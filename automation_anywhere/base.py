from requests import post, get

from automation_anywhere.errors import AuthenticationError


class Base:
    """This class is responsible for handling authentication on the AA360 cloud environment, and can help with more specific tasks."""
    def __init__(self, base_url: str):
        """Initialize the class.

        :param base_url: The AA360 Orchestrator URL
        :type base_url: str
        """
        self.token = None
        self.user_info = None
        self.headers = None
        self._base_url = base_url

    def authenticate(self, username: str, password: str, multiple_login: bool = False) -> tuple[bool, str]:
        """Authenticate the user via username/password and store the token internally on the "token" variable.

        :param username: The username to login to
        :type username: str
        :param password: The password to use to login the username
        :type password: str
        :param multiple_login: If set to True, we are stating that the user can have multiple logins, defaults to False
        :type multiple_login: bool, optional
        :return: A tuple depicting success, and an error if any
        :rtype: tuple[bool, str]
        """
        error = None
        success = False
        endpoint = f'{self._base_url}v1/authentication'
        payload = {
            'username': username,
            'password': password,
            'multiLogin': multiple_login
        }
        response = post(url=endpoint, json=payload)
        if response.status_code == 200:
            self.token = response.json()['token']
            self.user_info = response.json()['user']
            self.headers = {'X-Authorization': self.token}
            success = True
        elif response.status_code == 401:
            error = 'Unable to login: Invalid username/password'
        else:
            error = f'Unknown error: {response.json()["message"]}'
        return success, error

    def validate(self) -> tuple[bool, str]:
        """This method is used to validate if the aquired token is still valid. If it's not you need to login again.

        :return: A tuple depicting if the token is valid (bool) and a string to show any errors.
        :rtype: tuple[bool, str]
        """
        status = False
        error = None
        endpoint = f'{self._base_url}v1/authentication/token'
        query = {'token': self.token}
        response = get(url=endpoint, params=query)
        if response.status_code == 200:
            status = response.json()['valid']
        else:
            error = f'Unknown error: {response.json()["message"]}'
        return status, error

    def refresh(self) -> tuple[bool, str]:
        """Used to refresh the token, and restart the timeout with a new token. If the token is already expired, you can't use this method.

        :return: A tuple depicting if the process of refresh was a success, and a string to show any errors.
        :rtype: tuple[bool, str]
        """
        success = False
        error = None
        endpoint = f'{self._base_url}v1/authentication/token'
        payload = {
            'token': self.token
        }
        response = post(url=endpoint, json=payload)
        if response.status_code == 200:
            success = True
            self.token = response.json()['token']
            self.headers = {'X-Authorization': self.token}
        else:
            error = f'Unknown error: {response.json()["message"]}'
        return success, error

    def logout(self) -> tuple[bool, str]:
        """Logout the user and free the JWT on the AA control room.

        :return: A tuple depicting success for logging out, and a string for errors, if any
        :rtype: tuple[bool, str]
        """
        success = False
        error = None
        endpoint = f'{self._base_url}v1/authentication/logout'
        response = post(url=endpoint, headers=self.headers)
        if response.status_code == 204:
            success = True
        else:
            error = f'Unknown error: {response.json()["message"]}'
        return success, error
