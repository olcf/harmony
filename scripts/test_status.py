from scripts.job_status import JobStatus
from scripts import parse_file
from scripts.notifications.slack_app import slack_send
import os
import sys


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

    problems = False
    jobID_parser = parse_file.ParseJobID()
    for i in range(len(test_directories)):
        d = test_directories[i]
        jobID_path = os.path.join(d, 'job_id.txt')
        try:
            id = jobID_parser.parse_file(jobID_path)
        except FileNotFoundError:
            error_not_exist += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            problems = True
            continue

        if not in_queue(id):
            error_not_queued += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            problems = True

    error_str = error_not_exist + "\n\n" + error_not_queued
    if problems:
        slack_send.send_message(error_str)


def get_test_directories(tests_path, test_list):
    test_path_list = []
    for dic in test_list:
        path = os.path.join(tests_path, dic['program'], dic['test'], 'Status', 'latest')
        test_path_list.append(path)
    return test_path_list


def in_queue(jobid):
    JS = JobStatus()
    JS.init()
    jobs = JS.get_jobs(jobid=jobid, status=['eligible', 'current'])
    if len(jobs) != 0:
        return True
    else:
        return False


if __name__ == '__main__':
    rgt_in_path = sys.argv[1]
    while True:
        check_tests(rgt_in_path)
        os.sleep(300)
