from scripts.job_status import JobStatus
from scripts import parse_file
from scripts.notifications.slack_app import slack_send
import os
import sys
import time


# Check that each test in the rgt.input is running correctly.
def check_tests(rgt_in_path):
    # Create the parser for the rgt input.
    rgt_parser = parse_file.ParseRGTInput()
    # Get the test path and the list of tests.
    path_to_tests, test_list = rgt_parser.parse_file(rgt_in_path)
    # Get the directories for each test.
    test_directories = get_test_directories(path_to_tests, test_list)

    # Create an error string for each test that is not going to be run or is running.
    error_not_queued = "Tests not currently in queue or running:\n"
    # Create an error string for each test that does not exist.
    error_not_exist = "Tests that do not exist:\n"
    # Create booleans to check if there were any problems in either error possibility.
    queued_problems = False
    exist_problems = False

    # Create the parser for the jobID.
    jobID_parser = parse_file.ParseJobID()

    # Go through each directory and if it is a problem, add it to the correct error string.
    for i in range(len(test_directories)):
        # Get the path to the jobID.txt file.
        jobID_path = os.path.join(test_directories[i], 'job_id.txt')

        # Try to get the id of the file.
        try:
            id = jobID_parser.parse_file(jobID_path)
        # If the file does not exist then add it to the not_exist error string.
        except FileNotFoundError:
            error_not_exist += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            # There is now a problem.
            exist_problems = True
            continue

        # If the job is not in the queue/running then add it to the error string.
        if not in_queue(id):
            error_not_queued += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            # Another problem.
            queued_problems = True

    # Initialize the complete error string.
    error_str = ""
    # If there were existence problems then add it to the complete string.
    if exist_problems:
        error_str += error_not_exist + "\n"
    # If there were queue problems then add is to the complete string.
    if queued_problems:
        error_str += error_not_queued

    # If either problem existed then send a Slack message.
    if exist_problems or queued_problems:
        app = slack_send.SlackApp(os.environ["SLACK_BOT_TOKEN"])
        channel = "CCRA1Q41J"
        app.send_message(channel=channel, message=error_str)


# Get the directory for each test.
def get_test_directories(tests_path, test_list):
    # Initially no paths.
    test_path_list = []
    for dic in test_list:
        # Join the path_to_tests, the program for the test, the name of the test, Status, and latest.
        path = os.path.join(tests_path, dic['program'], dic['test'], 'Status', 'latest')
        # Add this path to the test list.
        test_path_list.append(path)
    return test_path_list


# Test if a certain jobID is in the queue/running.
def in_queue(jobID):
    # Initialize the status finder.
    JS = JobStatus()
    # Get all the jobs that match that jobID and are either eligible or current.
    jobs = JS.get_jobs(jobid=jobID, status=['eligible', 'current'])
    # If that job exists then all good.
    if len(jobs) != 0:
        return True
    else:
        return False


if __name__ == '__main__':
    # Try to get the path to the rgt input file.
    try:
        rgt_in_path = sys.argv[1]
    except IndexError:
        raise IndexError("No rgt.input file path set.")

    # Continuously check.
    while True:
        print("Sending message . . .")
        check_tests(rgt_in_path)
        # Sleep for a little while between checks.
        time.sleep(300)
