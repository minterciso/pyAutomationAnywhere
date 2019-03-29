# Automation Anywhere Python API Integration

## About
This Python module is used to talk to Automation Anywhere 10.5.x and start Tasks on selected machines.
What it does is basically call the Automation Anywhere REST API 2 times:
1. To login
2. To execute the task

Automation Anywhere does have a basic check if the task was "asked to be deployed" 
successfully, albeit very simple, it's still better then nothing.

## Install
There are some minimum dependencies:

    pip install pyodbc>=4.0 sqlalchemy>=1.3 requests>=2.21 

After installing them, you can proceed with the installation:

    pip install automation_anywhere

## Usage
As is, for the version 10.5.x, the API usage is basically:


    from automation_anywhere import base
    import logging
    
    logging.basicConfig(level=logging.DEBUG)

    try:
        aa = base.Executor(host='localhost', protocol='http', port=8080, username='bot_user', password='bot_password')
        aa.deploy_task(task='My Tasks\\Task1.atmx', client='BOTRUNNER01')
    except Exception as error:
        print(error)
        raise


The errors mainly come from the <code>requests()</code> that we create witht the JSON,
and while there are some errors from the Automation Anywhere side, they get back
 mainly as "Internal Error", unless it's username/password issues.

### What about task status?
The Automation Anywhere API (at least on version 10) does not return the task status, it only
returns the *deploy* status. Knowing that I did a little reverse engineering on the 
database, and came up with some simple queries that can check the status of the task.

There are a few caveats and warnings that you should know, before using this:
1) It'll block the execution, making it a sync execution, instead of async
2) You need to configure the ODBC directly for the Control Room database
3) There'll be a lot of queries to get the correct task ID, and status
4) This simply **does not** works on V11
5) This works, but it wasn't tested a lot, so there may be some bugs

If you want to, here's an example on how to use it
    
    from automation_anywhere import base
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        aa = base.Executor(host='localhost', protocol='http', port=8080, username='bot_user', password='bot_password')
        aa.database_options = {
            'DSN': 'CR_ODBC_LINK',
            'username': 'username',
            'password': 'password'
        }
        aa.set_check_status(True)
        if aa.deploy_task(task='My Tasks\\Task1.atmx', client='BOTRUNNER01') is False:
            logging.info('Task deploy or execution failed!')
        logging.info('Task return information:')
        logging.info('Status  : {status}'.format(status=aa.task_status['status']))
        logging.info('Complete: {complete}'.format(complete=aa.task_status['complete']))
        logging.info('Error   : {error}'.format(error=aa.task_status['error']))
    except Exception as error:
        print(error)
        raise
## Known issues
There's one big thing that needs to be taken account of, always: the Control Room
Credential Vault <b>must</b> be opened. If not, the Control Room API is unable
to deploy the task. The Automation Anywhere API however will return this simply
as an "Internal Error", so when this happens you need to go to the Control Room's
Audit Log and check for the error.

From our experience, 90% of the time the error is "Credential Vault not open". For 
fixing this the user simply has to login as admin on the "Control Room", so if you
use an admin user to check all those things, congratulations, by checking it you
already fixed it.

There is however an API call for checking if the Credential Vault is open or not, 
however this has proven extremely unreliable and there's no official documentation
for it, so I haven't added it here. Maybe on v11 of Automation Anywhere this is
executing better.

## About v11 of Automation Anywhere
While I was developing this simple Python module, Automation Anywhere released
the v11 of it's software. It has a lot of new and shiny things, however I wasn't
able to test it so far. That basically means that this *should* work, but I'll 
never guarantee it, until I've tested it.

## Todo
While I don't have a timeline (remember I'm *pro bono* here) there's a few things
I want to do (in no specific order):
* Test on v11
* Increase the ease of use of this module 