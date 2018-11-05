# Automation Anywhere Python API Integration

## About
This Python module is used to talk to Automation Anywhere 10.5.x and start Tasks on selected machines.
What it does is basically call the Automation Anywhere REST API 2 times:
1. To login
2. To execute the task

Automation Anywhere does have a basic check if the task was "asked to be deployed" successfully, albeit very simple, it's still better then nothing.

## Install
Just clone the code, and copy the automation_anywhere folder inside your topmost Python project.

## Usage
As is, for the version 10.5.x, the API usage is basically:


    from automation import automation_anywhere
    
    try:
        AA_api = automation_anywhere.AutomationAnywhere(username='bot_username', password='bot_password', 
                                                        protocol='http', host='localhost',port=8080)
        AA_api.executeTask(''My Tasks\\Test_task.atmx', 'BOTRUNNER001')
    except Exception as error:
        print(error)
        raise

The errors mainly come from the <code>requests()</code> that we create witht the JSON, and while there are some errors from the Automation Anywhere
side, they get back mainly as "Internal Error", unless it's username/password issues.

## Where's the code?
If you are reading this, that means that I haven't yet pushed the code. Why? Because I'm polishing it to be usefull for anyone. Please be patient,
this shouldn' take more than a day.
