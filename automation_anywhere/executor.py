from requests import post

from automation_anywhere.base import Base
from automation_anywhere.errors import AuthenticationError

class Executor(Base):
    """Class used to deploy (and hopefully execute) a bot on the AA360 control room"""
    def __init__(self, base_url: str, username: str, password: str, multiple_logins: bool = False):
        """The constructor.

        :param base_url: The AA360 ControlRoom URL.
        :type base_url: str
        :param username: The user used to deploy the bot.
        :type username: str
        :param password: The password to authenticate the user.
        :type password: str
        :param multiple_logins: If the user can and should have multiple logins, set to True, defaults to False
        :type multiple_logins: bool, optional
        :raises AuthenticationError: If there was an issue authenticating, it'll raise an AuthenticationError Exception
        """
        super().__init__(base_url=base_url)
        success, error = self.authenticate(
            username=username, password=password, multiple_login=multiple_logins)
        if success is False:
            raise AuthenticationError(error)

    def list_devices(self, sort: list = None, page: dict = None) -> tuple[list, dict, str]:
        """List all devices that can execute something. You need the user id of the device in order to execute something.

        :param sort: If set, it's a list that executes the sorting, defaults to None
        :type sort: list, optional
        :param page: If set, a dictionary with page parameters to add on the payload, defaults to None
        :type page: dict, optional
        :return: A tuple with a list of devices, a list of page data and a string to show errors
        :rtype: tuple[list, dict, str]
        """
        devices = None
        page_data = None
        error = None
        endpoint = f'{self._base_url}v1/devices/runasusers/list'
        payload = dict()
        payload['page'] = page
        payload['sort'] = sort if sort is not None else [
            {'field': 'username', 'direction': 'asc'}]
        response = post(url=endpoint, headers=self.headers, json=payload)
        if response.status_code == 200:
            page_data = response.json()['page']
            devices = response.json()['list']
        elif response.status_code == 400:
            error = f'Bad Request - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 401:
            error = f'Authentication Error - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 500:
            error = f'Server Error - {response.json()["code"]}: {response.json()["message"]}'
        else:
            error = f'Unknown error: {response.text}'
        return devices, page_data, error

    def list_automations(self, name: str = None, folder: str = 'public', filter: dict = None, sort: list = None, page: dict = None) -> tuple[list, dict, str]:
        """List all automations on the passed folder that the logged user can see. You need the file id parameters to start the deploy.

        :param name: The exact name of the automation, defaults to None
        :type name: str, optional
        :param folder: The folder to look for the automation, defaults to 'public'
        :type folder: str, optional
        :param filter: Extra filters to use, defaults to None
        :type filter: dict, optional
        :param sort: Sorting information, defaults to None
        :type sort: list, optional
        :param page: Paging information, defaults to None
        :type page: dict, optional
        :return: A tuple with the list of automations, the list of page information and a string to show errors if any.
        :rtype: tuple[list, dict, str]
        """
        automations = None
        page_data = None
        error = None
        if name is None and filter is None:
            error = 'At least "name" or "filter" must be present'
            return automations, page_data, error
        endpoint = f'{self._base_url}v2/repository/workspaces/{folder}/files/list'
        payload = dict()
        payload['page'] = page
        payload['sort'] = sort
        if name is not None:
            payload['filter'] = {
                'operator': 'eq',
                'field': 'name',
                'value': name
            }
        else:
            payload['filter'] = filter
        response = post(url=endpoint, json=payload, headers=self.headers)
        if response.status_code == 200:
            page_data = response.json()['page']
            automations = response.json()['list']
        elif response.status_code == 400:
            error = f'Bad Request - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 401:
            error = f'Authentication Error - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 404:
            error = f'Not Found - {response.json()["message"]}'
        else:
            error = f'Unknown error: {response.text}'
        return automations, page_data, error

    def deploy(self, automation_id: int, users_ids: list, pool_ids: list = None, override_default_device: bool = False, call_back_info: dict = None, bot_input: dict = None) -> tuple[bool, str, str, str]:
        """Actually deploy the automation on a number of bots.

        :param automation_id: The automation id to deploy.
        :type automation_id: int
        :param users_ids: A list with all the devices ids (called user id on the AA360) to execute the automation.
        :type users_ids: list
        :param pool_ids: A list of pool ids to work on, defaults to None
        :type pool_ids: list, optional
        :param override_default_device: If set to True, it'll ignore the default device configured on the automation, defaults to False
        :type override_default_device: bool, optional
        :param call_back_info: The information to configure the callback for the deploy data, defaults to None
        :type call_back_info: dict, optional
        :param bot_input: If the bot can receive any input, pass it here, defaults to None
        :type bot_input: dict, optional
        :return: A tuple with success, a string for errors and deployment id and deployment name
        :rtype: tuple[bool, str, str, str]
        """
        success = False
        error = None
        deployment_id = None
        automation_name = None
        endpoint = f'{self._base_url}v3/automations/deploy'
        payload = dict()
        payload['fileId'] = automation_id
        payload['runAsUserIds'] = users_ids
        payload['poolIds'] = pool_ids
        payload['callBackInfo'] = call_back_info
        payload['botInput'] = bot_input
        payload['overrideDefaultDevice'] = override_default_device
        response = post(url=endpoint, json=payload, headers=self.headers)
        if response.status_code == 200:
            deployment_id = response.json()['deploymentId']
            automation_name = response.json()['automationName']
            success = True
        elif response.status_code == 400:
            error = f'Bad Request - {response.json()["message"]}'
        elif response.status_code == 401:
            error = f'Authentication Error - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 404:
            error = 'Not Found'
        else:
            error = f'Unknown error: {response.text}'

        return success, error, deployment_id, automation_name

    def status(self, deploy_id: str = None, deploy_name: str = None, filter: dict = None, sort: list = None, page: dict = None) -> tuple[bool, str, dict]:
        """Check the status of an executed deploy. You can pass either deployment id or deployment name (if both are passed, it'll filter with all parameters), or any custom filter.

        :param deploy_id: The deployment id to search, defaults to None
        :type deploy_id: str, optional
        :param deploy_name: The deployment name to search, defaults to None
        :type deploy_name: str, optional
        :param filter: A custom filter to search, defaults to None
        :type filter: dict, optional
        :param sort: Sorting information, defaults to None
        :type sort: list, optional
        :param page: Paging information, defaults to None
        :type page: dict, optional
        :return: A tuple with success, an error message (if any) and the complete result from the activity/list endpoint
        :rtype: tuple[bool, str, dict]
        """
        success = False
        error = None
        return_data = dict()
        local_filter = {
            'operator': 'and',
            'operands': list()
            }
        if deploy_id:
            local_filter['operands'].append({
                'operator': 'eq',
                'field': 'deploymentId',
                'value': deploy_id
            })
        if deploy_name:
            local_filter['operands'].append({
                'operator': 'eq',
                'field': 'automationName',
                'value': deploy_name
            })
        payload = {
            'filter': filter if filter else local_filter,
            'page': page,
            'sort': sort
        }        
        endpoint = f'{self._base_url}v3/activity/list'
        response = post(url=endpoint, headers=self.headers, json=payload)
        if response.status_code == 200:
            return_data['executions'] = response.json()['list']
            return_data['page'] = response.json()['page']
            success = True
        elif response.status_code == 400:
            error = f'Bad Request - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 401:
            error = f'Authentication Error - {response.json()["code"]}: {response.json()["message"]}'
        elif response.status_code == 404:
            error = f'Not Found - {response.json()["message"]}'
        else:
            error = f'Unknown error: {response.text}'
        return success, error, return_data
    