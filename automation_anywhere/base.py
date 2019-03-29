import json
import requests
import logging
import sqlalchemy
import time

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
        self.__check_status = False
        self.database_options = {
            'DSN': None,
            'username': None,
            'password': None
        }
        self.automation_anywhere_version = 'v10'
        self.task_status={
            'status': None,
            'complete': None,
            'error': None
        }
        self.__database_conn = None

    def __connect_to_database(self):
        """
        Simply connects to the database.
        """
        # Prevents execution if we are in a different version than v10 of Automation Anywhere Control Room
        if self.automation_anywhere_version != 'v10':
            return -1
        if self.__database_conn is not None:
            return
        try:
            db_connection = 'mssql+pyodbc://{username}:{password}@{dsn}'.format(
                username=self.database_options['username'],
                password=self.database_options['password'],
                dsn=self.database_options['DSN']
            )
            self.__database_conn = sqlalchemy.create_engine(db_connection)
        except Exception as error:
            self.__logger.error('Error connecting to database: {err}'.format(err=error))
            raise

    def __get_task_cache(self, task: str, client: str):
        """
        It seems that there's a kind of cache when it starts a new task. Get all the IDs that are possible to be used by this cache

        :param task: The task name as passed to the API
        :param client: The client that the task is suposed to run
        :return: A list of IDs that can be used as cache
        """
        # Prevents execution if we are in a different version than v10 of Automation Anywhere Control Room
        if self.automation_anywhere_version != 'v10':
            return -1
        fname = task.split('\\')[-1]
        self.__logger.debug('Looking for cache for task \'{fname}\''.format(fname=fname))
        query = 'select trd.Id as id from TaskRunDetails trd, Tasks t, Clients c, Users u where	' \
                'trd.TaskId=t.id and trd.ClientId=c.id and trd.UserId=u.id and ClientStatus=0 and IsTaskExecutionCompleted=0 and ' \
                'u.UserName=\'{username}\' and c.HostName=\'{client}\' and t.FileName=\'{filename}\''.format(username=self.__username,
                                                                                                             client=client,
                                                                                                             filename=fname
                                                                                                             )
        try:
            row = self.__database_conn.execute(query).fetchall()
            cache = []
            for r in row:
                cache.append(r['id'])
            if len(cache) > 0:
                self.__logger.debug('Got cache ids: {cache}'.format(cache=','.join([str(x) for x in cache])))
                return cache
            return None
        except Exception as error:
            self.__logger.error('Unable to execute query {query}:{err}'.format(query=query, err=error))
            raise

    def __get_task_id(self, task: str, client: str, cache: list = None):
        """
        Tries to get the task id. This is by far the most complex method for this. It seems that on the Automation Anywhere v10.5 there's a kind of
        "cache" to try to expedite the task execution. So every time a task starts via the API, a new line on the TaskRunDetails table is created, the
        strange part is that sometimes this line is not used, and sometimes it is. It seems that it is used when the task takes some time to execute
        (ie: more then 5 seconds), and it's not used when it's actually a really fast task. So basically we keep querying the cache and, if the cache
        hasn't any update, we query anything with the ID bigger than the cache. If there's no cache however, we make a simple query and return it's id

        :param task: The task name, as passed on the API to start
        :param client: The client name
        :param cache: A list with the cache ids
        :return: The task ID created on the Automation Anywhere Control Room
        """
        # Prevents execution if we are in a different version than v10 of Automation Anywhere Control Room
        if self.automation_anywhere_version != 'v10':
            return -1
        fname = task.split('\\')[-1]
        if cache is not None:
            cache.sort(reverse=True)
            try:
                task_id = -1
                while task_id < 0:
                    query = 'select trd.Id as id from TaskRunDetails trd where ' \
                            'trd.Id in ({ids}) ' \
                            'and IsTaskExecutionCompleted=0 and StartTime is not NULL'.format(ids=','.join([str(x) for x in cache]))
                    row = self.__database_conn.execute(query).fetchone()
                    if row is not None:
                        task_id = row['id']
                    else:
                        # Maybe the task finished already, without using the cache, check for this
                        query = 'select trd.Id as id from TaskRunDetails trd , Tasks t, Clients c, Users u where ' \
                                'trd.TaskId=t.id and trd.ClientId=c.id and trd.UserId=u.id and ' \
                                'u.UserName=\'{username}\' and c.HostName=\'{client}\' and t.FileName=\'{filename}\' ' \
                                'and trd.IsTaskExecutionCompleted=1 and trd.Id > {task_id} ' \
                                'order by Id desc'.format(username=self.__username,
                                                          client=client,
                                                          filename=fname,
                                                          task_id=cache[0]
                                                          )
                        row = self.__database_conn.execute(query).fetchone()
                        if row is not None:
                            task_id = row['id']
                return task_id
            except Exception as error:
                self.__logger.error('Unable to execute query {query}:{err}'.format(query=query, err=error))
                raise
        else:
            self.__logger.debug('There\'s no cache for the task \'{task}\'. Waiting for task to arrive on database...'.format(task=fname))
            query = 'select trd.Id as id from TaskRunDetails trd , Tasks t, Clients c, Users u where ' \
                    'trd.TaskId=t.id and trd.ClientId=c.id and trd.UserId=u.id and ' \
                    'u.UserName=\'{username}\' and c.HostName=\'{client}\' and t.FileName=\'{filename}\' ' \
                    'and trd.IsTaskExecutionCompleted=0 and trd.StartTime is not NULL ' \
                    'order by Id desc'.format(username=self.__username,
                                              client=client,
                                              filename=fname
                                              )
            task_id = -1
            try:
                row = self.__database_conn.execute(query).fetchone()
                if row is not None:
                    return row['id']
                return task_id
            except Exception as error:
                self.__logger.error('Unable to execute query {query}:{err}'.format(query=query, err=error))
                raise

    def __get_task_status(self, task_id: int):
        """
        Get's the task status, via the passed task id.

        :param task_id: The task id to query status from
        :return: A dictionary with 'status','complete' and 'error' keys.
        """
        # Prevents execution if we are in a different version than v10 of Automation Anywhere Control Room
        if self.automation_anywhere_version != 'v10':
            return -1
        query = 'select trd.Status as status, trd.IsTaskExecutionCompleted as completed, trd.ErrorMessage as error ' \
                'from TaskRunDetails trd ' \
                'where trd.Id={t_id}'.format(t_id=task_id)
        try:
            row = self.__database_conn.execute(query).fetchone()
            if row is not None:
                return {
                    'status': row['status'],
                    'complete': (False if row['completed'] == 0 else True),
                    'error': row['error']
                }
            return None
        except Exception as error:
            self.__logger.error('Unable to execute query {query}:{err}'.format(query=query, err=error))
            raise

    def set_check_status(self, check: bool):
        """
        Set's the check status and, if wanted it'll check on the database (of v10.5) for the task status

        :param check: True or False, if True it'll connect to the database using the database_options param
        """
        if check:
            self.__connect_to_database()
            self.__check_status = True
            if self.automation_anywhere_version != 'v10':
                self.__logger.info('Currently task status check is only supported on version 10.')
                self.__logger.info(
                    'You configured the version to be \'{version}\'.'.format(version=self.automation_anywhere_version))
                self.__check_status = False
                return
        else:
            self.__check_status = False
            self.__database_conn = None

    def get_check_status(self):
        return self.__check_status

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
        if self.__check_status:
            # Get the "cache" of tasks
            cache = None
            cache = self.__get_task_cache(task, client)
            self.__logger.info('Getting task status...')
            task_id = -1
            while task_id < 0:
                task_id = self.__get_task_id(task=task, client=client, cache=cache)
                time.sleep(1)
            self.__logger.info('Got task ID {t_id}.'.format(t_id=task_id))
            self.__logger.debug('Waiting for task to complete...')
            self.task_status = self.__get_task_status(task_id)
            while self.task_status['complete'] is False:
                time.sleep(1)
                self.task_status = self.__get_task_status(task_id)
            if self.task_status['status'] == 'Completed':
                return True
            return False
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
