import unittest
from unit_tests import test_job_monitor
from unit_tests import test_job_status
from unit_tests import test_parse_file
from unit_tests import test_test_status
from unit_tests.notifications_tests import test_slack_commands
from unit_tests.database_tests import test_create_database
from unit_tests.database_tests import test_update_database
import argparse


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='fast', action='store_true', default=False, help='Only run fast tests.')
    parser.add_argument('-d', dest='database', action='store_true', default=False, help='Only run database tests.')

    return parser


def main():
    parser = make_parser()
    args = parser.parse_args()

    # TODO: Should this be split more than this?
    fast_test_list = [test_job_status.TestJobClass, test_job_status.TestJobStatus,
                      test_parse_file.TestErrors, test_parse_file.TestParseJobID, test_parse_file.TestParseRGTInput,
                      test_test_status.TestTestStatus,
                      test_slack_commands.TestMessageParser, test_slack_commands.TestStaticFunctions]

    database_test_list = [test_create_database.TestCreateDatabase,
                          test_update_database.TestUpdateDatabase]

    slow_test_list = [test_job_monitor.TestJobMonitorClass, test_job_monitor.TestMonitor]

    if args.fast:
        test_list = fast_test_list
        print("Only running fast tests.")
    elif args.database:
        test_list = database_test_list
        print("Only running database tests.")
    else:
        test_list = fast_test_list + slow_test_list + database_test_list

    message = "Running tests in these cases:"
    for test in test_list:
        message += "\n " + test.__name__
    print(message)

    test_load = unittest.TestLoader()

    case_list = []
    for test_case in test_list:
        test_suite = test_load.loadTestsFromTestCase(test_case)
        case_list.append(test_suite)

    full_suite = unittest.TestSuite(case_list)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(full_suite)


if __name__ == '__main__':
    main()
