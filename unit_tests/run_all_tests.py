import unittest
from unit_tests import test_job_monitor
from unit_tests import test_job_status
from unit_tests import test_parse_file
from unit_tests import test_test_status
from unit_tests.notifications_tests import test_slack_commands

def main():
    # TODO: Split these into types of tests to run and order them correctly.
    test_list = [test_job_monitor.TestJobMonitorClass, test_job_monitor.TestMonitor,
                 test_job_status.TestJobClass, test_job_status.TestJobStatus,
                 test_parse_file.TestErrors, test_parse_file.TestParseJobID, test_parse_file.TestParseRGTInput,
                 test_test_status.TestTestStatus,
                 test_slack_commands.TestMessageParser, test_slack_commands.TestStaticFunctions]

    test_load = unittest.TestLoader()

    case_list = []
    for test_case in test_list:
        test_suite = test_load.loadTestsFromTestCase(test_case)
        case_list.append(test_suite)

    full_suite = unittest.TestSuite(case_list)

    runner = unittest.TextTestRunner()
    runner.run(full_suite)


if __name__ == '__main__':
    main()
