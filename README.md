# Automation Anywhere Python API Integration

## About
This Python module is used to talk to Automation Anywhere 360 and start Tasks on selected machines.

Automation Anywhere does have a basic check if the task was "asked to be deployed" 
successfully, albeit very simple, it's still better then nothing.

## Install
There are some minimum dependencies:

    pip install requests>=2.21 

After installing them, you can proceed with the installation:

    pip install automation_anywhere

## Usage
As is, for the version 360, you can use the package to deploy a task as such:


    from automation_anywhere.executor import Executor
    base_url = 'https://your-automation-controlroom-url/'
    username = 'your-username'
    password = 'your-password'
    aa_executor = Executor(base_url, username, password)
    devices, _, error = aa_executor.list_devices()
    if error is not None:
      # handle the error
      pass
    automations, _, error = aa_executor.list_automations(name='Test')
    if error is not None:
      # handle the error
      pass
    # Get the device id to execute, we'll just get the first one
    device_id = int(devices[0]['id'])
    # Get the automation id to execute, we'll just get the first one
    automation_id = int(automations[0]['id'])
    # Deploy
    success, error, deployment_id, deployment_name = aa_executor.deploy(automation_id, [device_id])
    if success:
      # handle the error
      pass
    else:
      print(f'Deployed on id {deployment_id} with name {deployment_name}')
    aa_executor.logout()
    


The errors will come 100% from the APIs of the Control Room.

### What about task status?
I found an endpoint where you can get the job execution status, by filtering it via deployment id or deployment name. Here's a sample usage:

    from automation_anywhere.executor import Executor
    base_url = 'https://your-automation-controlroom-url/'
    username = 'your-username'
    password = 'your-password'
    deploy_id = '377b04a5-fa8b-4e4a-8db5-8d769fd6639b'
    deploy_name = 'Test.2023.05.19.17.28.51.minterciso@deloitte.com'
    aa_executor = Executor(base_url, username, password)
    success, error, data = aa_executor.status(deploy_id=deploy_id)

And the dictionary output:

    [{'automationId': '',
    'automationName': 'Test.2023.05.19.17.28.51.minterciso@deloitte.com',
    'automationPriority': 'PRIORITY_MEDIUM',
    'botLabel': '',
    'callbackInfo': '',
    'canManage': True,
    'command': 'logToFile',
    'createdBy': '41',
    'createdOn': '2023-05-19T17:28:51.949121Z',
    'currentBotName': 'Test',
    'currentLine': 1,
    'deploymentId': '377b04a5-fa8b-4e4a-8db5-8d769fd6639b',
    'deviceId': '10',
    'deviceName': 'utils',
    'endDateTime': '2023-05-19T17:29:23.438893600Z',
    'fileId': '459',
    'fileName': 'Test',
    'filePath': '',
    'id': '5a3823af-3495-4692-9a08-0da80e70f046_06a59328ad01bfaa',
    'message': '',
    'modifiedBy': '41',
    'modifiedOn': '2023-05-19T17:29:25.115503Z',
    'progress': 100,
    'queueId': '',
    'queueName': '',
    'runElevated': False,
    'startDateTime': '2023-05-19T17:29:21.602952600Z',
    'status': 'COMPLETED',
    'tenantUuid': '0a662aeb-8728-11a9-8187-bed41445010e',
    'totalLines': 1,
    'type': 'RUN_NOW',
    'userId': '41',
    'userName': 'minterciso@deloitte.com',
    'usingRdp': False}]

Basically it's a list with all executions found with the filter, and all their status.