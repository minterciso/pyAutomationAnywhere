import json
import requests
import logging

from . import errors


class Executor:
    """
    This class is responsible to call and execute a task on the Automation Anywhere API.
    It currently works with Automation Anywhere Control Room 10.5.4 and Automation Anywhere Client 10.7

    :note: It needs the Credential Vault to be opened

    :param protocol: The protocol that consists the Control Room URL (ie: http)
    :param host: The host where the control room is available
    :param port: The port where the control room is available
    :param username: The Bot Runner username with the API permissions
    :param password: The Bot Runner password with the API permissions
    """

    def __init__(self, protocol: str, host: str, port: int, username: str, password: str):
        self.__api = {
            'authentication': 'controlroomapi/v1/authenticate',
            'deployment': 'controlroomapi/v1/deploy'
        }
        self.__url = protocol + '://' + host + ':' + str(port)
        self.__username = username
        self.__password = password
        self.__auth_info = {
            'request_code': 0,
            'request_text': '',
            'request_token': ''
        }
        self.__deploy_info = {
            'request_code': 0,
            'request_text': ''
        }
        self.__logger = logging.getLogger()

    def deploy_task(self, task: str, client: str):
        """
        Connects and executes the task passed

        :param task: The task we want to execute
        :param client: The client machine to connect and run the task (currently is supported only one client at a time)
        :return: True if success, otherwise it raises an Exception
        """
        self.__logger.info('Authenticating and executing task \'%s\'...', task)
        try:
            self.__authenticate()
        except Exception as error:
            self.__logger.error('Unable to authenticate: %s', str(error))
            raise
        self.__logger.info('Deploying on client \'%s\'', client)
        deploy_data = {
            'taskRelativePath': task,
            'botRunners': [{'client': client, 'user': self.__username}]
        }
        deploy_headers = {
            'Content-Type': 'application/json',
            'X-Authorization': self.__auth_info['request_token']
        }
        deploy_json = json.dumps(deploy_data)
        try:
            r = requests.post(self.__url + '/' + self.__api['deployment'], data=deploy_json, headers=deploy_headers)
        except Exception as error:
            self.__logger.error('Unable to send POST request to Control Room: %s', str(error))
            raise
        self.__deploy_info['request_code'] = r.status_code
        self.__deploy_info['request_text'] = r.text
        if r.status_code != 200:
            self.__logger.info('Invalid response: %d', r.status_code)
            self.__logger.info('Reason: %s', r.reason)
            self.__logger.info('Description: %s', r.text)
            raise errors.Error(r.reason)
        return True

    def __authenticate(self):
        """
        This method authenticates on the Control Room API

        :return: True if sucessfull, otherwise it raises an Exception
        """
        self.__logger.info('Authenticating on controlroom \'%s\' with username \'%s\'', self.__url, self.__username)
        self.__logger.debug('Using password \'%s\'', self.__password)
        auth_data = {
            'username': self.__username,
            'password': self.__password
        }
        auth_json = json.dumps(auth_data)
        auth_headers = {'Content-type': 'application/json'}
        try:
            r = requests.post(self.__url + '/' + self.__api['authentication'], data=auth_json, headers=auth_headers)
        except Exception as error:
            self.__logger.error('Unable to send POST request to Control Room: %s', str(error))
            raise
        self.__auth_info['request_code'] = r.status_code
        self.__auth_info['request_text'] = r.text
        if r.status_code != 200:
            self.__logger.info('Invalid response: %d', r.status_code)
            self.__logger.info('Reason: %s', r.reason)
            self.__logger.info('Description: %s', r.text)
            raise errors.Error(r.reason)
        self.__auth_info['request_token'] = r.json()['token']
        return True
