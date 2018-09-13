from scripts.job_status import JobStatus
from scripts import parse_file
from scripts.notifications import slack_send
import os
import sys

def check_tests(rgt_in_path):
    rgt_parser = parse_file.ParseRGTInput()
    path_to_tests, test_list = rgt_parser.parse_file(rgt_in_path)
    test_directories = get_test_directories(path_to_tests, test_list)

    ids = []
    jobID_parser = parse_file.ParseJobID()
    for d in test_directories:
        jobID_path = os.path.join(d, 'job_id.txt')
        ids.append(jobID_parser.parse_file(jobID_path))

    not_queued = []
    for i in range(len(ids)):
        if not in_queue(ids[i]):
            not_queued.append(test_list[i])

    error_str = "Tests not currently in queue or running:\n"
    for nq in not_queued:
        error_str += "\t" + nq['program'] + "\t" + nq['test'] + "\n"

    if len(not_queued) != 0:
        slack_send.send_message(error_str)
        print(error_str)
    else:
        print("All tests running.")


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
    check_tests(rgt_in_path)
