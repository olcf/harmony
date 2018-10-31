# harmony

harmony is a HARness MONitoring sYstem that is used to monitor the OLCF harness
during acceptance.

## Ideas:
* Develop in Python, easier to extend if needed.
* We can query the rgt_status database
* The database should be an environment variable and changeable
* If we have two people starting the harness from the same directory and point 
to the same database and there is a conflict, does it get corrupted?
  * If we use a real database, this should not be an issue.
* We can create a database on OpenShift.

## Database Schema
- Tables:
  - RGTstatus: 
    - key: Harness UniqueID: we could change in future.
    - Test ID
    - Datetime
    - Harness start time
    - JobID
    - App name
    - Test name
    - Build Status
    - Submit Status
    - Harness Job Status
    - LSF Job Status
    - Flag for record completed
    
  - Events: key is a combination of Event ID and Harness ID.
    - Event Unique ID
    - Event Type ID
    - Datetime
    - Event time
    - Harness UniqueID   

  - Events Types:
    - key: Event ID
    - Type of Event

  - Status Types:
    - key: Status ID
    - Status Name
    - Status Value
    
  - Application:
    - Unique ID
    - App Name
    
  - Tests:
    - Unique ID
    - App ID
    - Test Name
    
## Action Items
- Status directory:
  - Concerns that putting the Status directory and files in GPFS may not be as
    reliable.
  - Reuben: we could do something like xalt.
    - Parse the files to collect the test data from Status, Run_Archive.
- What do we want to do?
  - Get the time stamps from begin/end of the application launch.
  - One database that will collect 
- How do we distinguish from different harness sessions?
  - Session tag
  - Current working directory
  - App directory
  - Scratch directory
  - We could have runtests.py write to the config: environment variables and RGT
    input file.
  - Create account for Reuben on mariadb.
  - Ask Don to install MySQL and Python-MySQL from login node.
- Who is doing what? ToDo:
  - Schema for the database
  - Status file parsing
  - Monitor queue script

## Running Stuff
#### Unit Tests
- Run unittests using `python3 -m unit_tests.run_all_tests` while in the harmony directory. 
Add the `-f` flag to the end to only run fast tests.
Add the `-d` flag to run only database tests.

#### Create Config
Run `python3 -m scripts.config_functions` in the harmony directory.
  
#### Application
- Run the slack application using `python3 -m run_slack_app` while in the harmony directory.

#### Database
- Run harmony using `python3 -m run_harmony -u <username> -p <password> -r <rgt_input_path>` 
while in the harmony directory. The `<username>` and `<password>` are those used for connection to the database.
