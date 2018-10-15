"""
This file gets all the tests that need to be checked whenever the database is refreshed.
It deals with tests already in the database and deals with adding new tests to the database
as long as they are pointed to by the rgt input file.
"""
from scripts import parse_file
from scripts import test_status
import os
import warnings


class testFinder:
    """
    This class finds all tests in an rgt path and makes sure that each of the test instances
    exists in the database and if not, adds them.
    """
    # TODO: Choose whether to pass connector around or pass database around.
    def __init__(self, connector, rgt_input_path, rgt_test_table='rgt_test'):
        """
        Constructor

        :param connector: A database connector that is set up to connect.
        :param rgt_input_path: The path where the rgt.input file is located.
        :param rgt_test_table: The table that should be looked in for tests.
        """
        self.db = connector.connect()
        self.rgt_input_path = rgt_input_path
        self.rgt_test_table = rgt_test_table

    def add_new_tests(self):
        """
        Add all tests from the rgt.input file that are not yet in the database.

        :return:
        """
        # Get the test directories from the file.
        test_directories = self.get_test_dirs_from_rgt()

        # For each test directory, add any new UIDs from that test.
        for test_dir in test_directories:
            self.add_new_uids(test_dir)

    def get_test_dirs_from_rgt(self):
        """
        Get the directories to each test. Each directory is appended with '/Status/' since we
        do not need any info from the directory above.

        :return: A list of test directories.
        """
        # Create the parser.
        parser = parse_file.ParseRGTInput()
        # Get the path to tests and the list of tests.
        path_to_tests, test_list = parser.parse_file(self.rgt_input_path)
        # Get the test directories.
        test_directories = test_status.get_test_directories(path_to_tests, test_list, append_dirs=('Status'))
        return test_directories

    def add_new_uids(self, test_path):
        """
        Get all uids for some test.

        :param test_path: Path to test ending in /Status/. This is the path just before
        entering any actual test instance.
        :return:
        """
        # TODO: Should it just warn when a the path to the test does not exist or should I let it error?
        if not os.path.exists(test_path):
            warnings.warn("Could not find path to this test.\n" + test_path)
            return

        # Create the path.
        rgt_status_path = os.path.join(test_path, 'rgt_status.txt')
        # Create the parser.
        rgt_parser = parse_file.ParseRGTStatus()
        # Get the dictionaries for each line in the status file.
        job_dics = rgt_parser.parse_file(rgt_status_path)

        # For each line in the file, add it to the table if it is new.
        for job_dic in job_dics:
            # Get the uid for the test.
            harness_uid = job_dic['harness_uid']
            # Test if test instance exists in database.
            if not self.uid_in_table(harness_uid):
                # If it does not, add it.
                job_path = os.path.join(test_path, harness_uid)
                self.add_to_table(job_dic, job_path)

    def add_to_table(self, job_dic, job_path):
        """
        Add a test to the table where tests are stored.

        :param job_dic: Dictionary for the job.
        :param job_path: Path to where the instance is located.
        :return:
        """
        # Create an event parser.
        PE = parse_file.ParseEvent()
        # Parse Event 110 to get all info for insertion into table.
        event_dic = PE.parse_file(os.path.join(job_path, 'Event_110_logging_start.txt'))

        # Set the necessary variables for input into the table.
        harness_uid = job_dic['harness_uid']
        harness_start = job_dic['harness_start']
        harness_tld = job_path
        application = event_dic['app']
        testname = event_dic['test']
        system = event_dic['rgt_system_log_tag']

        # Create a cursor for executing commands on the table.
        cursor = self.db.cursor()
        # Insert into the table the values found.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, application, testname, system, done) " \
              "VALUES ({harness_uid}, {harness_start}, {harness_tld}, {application}, {testname}, {system}, FALSE )"\
              .format(table=self.rgt_test_table, harness_uid=harness_uid, harness_start=harness_start,
                      harness_tld=harness_tld, application=application, testname=testname, system=system)

        # Execute the command.
        cursor.execute(sql)
        # Commit it to the database so that it is updated.
        self.db.commit()

    def uid_in_table(self, uid):
        """
        Test if some uid is in a table.

        :param uid: UID to search for
        :return: A boolean if it is or isn't.
        """
        # Create a cursor for executing commands on the database.
        cursor = self.db.cursor()
        # Select 1 or 0 depending if the uid exists.
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE harness_uid = {uid} )"\
            .format(table=self.rgt_test_table, uid=uid)

        # Execute the command.
        cursor.execute(sql)
        # Get the result.
        in_table = cursor.fetchone()
        if in_table:
            return True
        else:
            return False
