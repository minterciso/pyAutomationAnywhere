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
    base_url = 'https://your-automation-controlroom-url'
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
I'm still trying to figure out how this works on AA360. So for now, there's nothing regarding this.