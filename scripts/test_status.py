from scripts.job_status import JobStatus
from scripts import parse_file
from scripts.notifications.slack_app import slack_send
import os
import sys
import time

def check_tests(rgt_in_path):
    rgt_parser = parse_file.ParseRGTInput()
    path_to_tests, test_list = rgt_parser.parse_file(rgt_in_path)
    test_directories = get_test_directories(path_to_tests, test_list)

    error_not_queued = "Tests not currently in queue or running:\n"
    error_not_exist = "Tests that do not exist:\n"
    queued_problems = False
    exist_problems = False
    jobID_parser = parse_file.ParseJobID()
    for i in range(len(test_directories)):
        d = test_directories[i]
        jobID_path = os.path.join(d, 'job_id.txt')
        try:
            id = jobID_parser.parse_file(jobID_path)
        except FileNotFoundError:
            error_not_exist += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            exist_problems = True
            continue

        if not in_queue(id):
            error_not_queued += "\t" + test_list[i]['program'] + "\t" + test_list[i]['test'] + "\n"
            queued_problems = True

    error_str = ""
    if exist_problems:
        error_str += error_not_exist + "\n"
    if queued_problems:
        error_str += error_not_queued

    if exist_problems or queued_problems:
        app = slack_send.SlackApp(os.environ["SLACK_BOT_TOKEN"])
        channel = "CCRA1Q41J"
        app.send_message(channel=channel, message=error_str)


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
    try:
        rgt_in_path = sys.argv[1]
    except IndexError:
        raise IndexError("No rgt.input file path set.")

    while True:
        print("Sending message . . .")
        check_tests(rgt_in_path)
        time.sleep(300)
