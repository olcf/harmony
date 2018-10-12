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
    def __init__(self, connector, rgt_path):
        self.db = connector.connect()
        self.rgt_path = rgt_path

    def get_test_uids(self, test_path):
        """
        Get all uids for some test.

        :param test_path: Path to test ending in /Status. This is the path just before
        entering any actual test instance.
        :return: A list of uids for the test.
        """
        if not os.path.exists(test_path):
            warnings.warn("I couldn't find this path. " + test_path)
            return []

        rgt_status_path = os.path.join(test_path, 'rgt_status.txt')
        rgt_parser = parse_file.ParseRGTStatus()
        job_dics = rgt_parser.parse_file(rgt_status_path)

        jobs_to_add = []
        for job_dic in job_dics:
            harness_uid = job_dic['harness_uid']
            # Test if test instance exists.
            if os.path.exists(os.path.join(test_path, harness_uid)):
                if not self.uid_in_table(harness_uid):
                    jobs_to_add.append(job_dic)

    def add_to_table(self, variables, values, table='rgt_test'):

    def uid_in_table(self, uid, table='rgt_test'):
        """
        Test if some uid is in a table.

        :param uid: UID to search for
        :param table: Table to look in.
        :return: A boolean if it is or isn't.
        """
        cursor = self.db.cursor()
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE harness_uid = {uid} )".format(table=table, uid=uid)

        cursor.execute(sql)
        in_table = cursor.fetchone()
        if in_table:
            return True
        else:
            return False
