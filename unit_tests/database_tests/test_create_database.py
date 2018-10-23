import unittest
import os
from scripts.database import create_database
from scripts.database import connect_database
from scripts import config_functions


class TestCreateDatabase(unittest.TestCase):
    """
    Class to test functions in create_database.py
    """

    def setUp(self):
        self.create_tables_path = os.path.join(os.path.dirname(__file__), 'create_test_tables.sql')

        database_conf = config_functions.get_config()['DATABASE']
        self.connector = connect_database.DatabaseConnector(database_conf['host'], database_conf['user'],
                                                            database_conf['password'], database_conf['database_name'])

    def testCreateTables(self):
        create_database.create_db(self.connector, self.create_tables_path)

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "SHOW TABLES"

        cursor.execute(sql)
        # This contains a tuple of tuples.
        tables = cursor.fetchall()

        tables = [table[0] for table in tables]

        self.assertIn('test_rgt_event', tables)
        self.assertIn('test_rgt_check', tables)
        self.assertIn('test_rgt_test', tables)
        self.assertIn('test_rgt_test_event', tables)

    def tearDown(self):
        drop_tables_path = os.path.join(os.path.dirname(__file__), 'drop_test_tables.sql')
        create_database.execute_sql_file(connector=self.connector, file_path=drop_tables_path)
