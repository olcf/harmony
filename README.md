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
  - Test instances:
    - Unique ID
    - Date
    - Harness UniqueID
    - JobID
    - Event ID
    - App name
    - Test name
    - Build Status
    - Submit Status
    - Job Status
  - Events:
    - Event ID
    - Type of Event
  - Status:
    - Status ID
    - Status Name
    
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

## Unit Tests
- Run unittests using 'python -m unittest discover unit_tests "test_*.py"' while in the harmony directory.
  
