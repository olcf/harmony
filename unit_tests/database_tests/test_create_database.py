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
        """
        Set the necessary variables for later use.
        """
        # The path to where the sql file for creating the tables is.
        self.create_tables_path = os.path.join(os.path.dirname(__file__), 'create_test_tables.sql')

        # The config for the database.
        database_conf = config_functions.get_config()['CLIENT']
        # Initialize a connector.
        self.connector = connect_database.DatabaseConnector(database_conf)

    def testCreateTables(self):
        """
        Test whether the tables can be created correclty.
        """
        # Create the database.
        create_database.create_db(self.connector, self.create_tables_path)

        # Connect to the database and get the tables in it.
        db = self.connector.connect()
        cursor = db.cursor()
        sql = "SHOW TABLES"

        cursor.execute(sql)
        # This contains a tuple of tuples.
        tables = cursor.fetchall()

        tables = [table[0] for table in tables]

        # Check that each of the expected tables are in there.
        self.assertIn('test_rgt_event', tables)
        self.assertIn('test_rgt_check', tables)
        self.assertIn('test_rgt_test', tables)
        self.assertIn('test_rgt_test_event', tables)

    def tearDown(self):
        """
        Clear the created tables from the database.
        """
        drop_tables_path = os.path.join(os.path.dirname(__file__), 'drop_test_tables.sql')
        create_database.execute_sql_file(connector=self.connector, file_path=drop_tables_path)
