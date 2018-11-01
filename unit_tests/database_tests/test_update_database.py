import unittest
import os
from scripts.database import update_database
from scripts.database import create_database
from scripts import config_functions
from scripts.database import connect_database
import shutil
from random import random
from contextlib import contextmanager
import signal
import copy


class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    """
    Limit the amount of time some command can take.

    :param seconds: The number of seconds allowed for the command.
    """
    def signal_handler(signum, frame):
        """
        Raise an exception when called.

        :param signum: The signal type.
        :param frame: The handler for the signals.
        """
        raise TimeoutException("Timed out.")
    # Initialize a signal.
    signal.signal(signal.SIGALRM, signal_handler)
    # Set the alarm.
    signal.alarm(seconds)
    # Let the wrapped command run. If it has not finished in time, alarm.
    try:
        yield
    finally:
        signal.alarm(0)


class InstanceCreator:
    """
    Class for creating test instances.
    """
    class Instance:
        """
        Class for holding all paths for some instance.
        """
        # TODO: Make this class hold stuff in a cleaner fashion.
        def __init__(self):
            return

    def __init__(self):
        """
        Initialize the paths used for some instance.
        """
        self.path_to_inputs = os.path.abspath(os.path.join(__file__, '..', '..', 'test_inputs', 'database_inputs'))
        self.path_to_rgt_input = os.path.join(self.path_to_inputs, 'rgt_input.txt')
        self.path_to_lsf_files = os.path.join(self.path_to_inputs, 'lsf_files')
        self.path_to_output_files = os.path.join(self.path_to_inputs, 'output_files')
        self.path_to_example_tests = os.path.join(self.path_to_inputs, 'example_tests_for_database')

    def create_test_instance(self, program_name, test_name, instance_name, time, job_id, build_status, submit_status,
                             check_status, outputs, system, events, exit_status, in_queue):
        """
        Create an instance of some test that can be used for testing.

        :param program_name: The name of the program.
        :param test_name: The name of the application.
        :param instance_name: The name of the instance. This is like the harness uid.
        :param time: The time when this test began.
        :param job_id: The id for this test in LSF.
        :param build_status: The build status for this test.
        :param submit_status: The submit status for this test.
        :param check_status: The check status for this test.
        :param outputs: A dictionary containing the different outputs of some test.
        :param system: The system being run on.
        :param events: A dictionary containing dictionaries for each event for some test.
        :param exit_status: The exit status of the test.
        :return: The created instance.
        """
        # Initialize an instance holder.
        instance = self.Instance()
        # Make the necessary directories for the test and set the status and run_archive paths for the test.
        instance.run_archive_instance_path, instance.status_instance_path = \
            self.make_directories(program_name, test_name, instance_name, self.path_to_example_tests)

        # Set the path to where the tests rgt status is.
        instance.path_to_rgt_status = os.path.join(os.path.dirname(instance.status_instance_path), 'rgt_status.txt')
        # Write the rgt status line for the test.
        self.write_rgt_status(instance.path_to_rgt_status, time, instance_name, job_id,
                              build_status, submit_status, check_status)

        # Write the rgt input line for the test.
        self.write_rgt_input(self.path_to_rgt_input, self.path_to_example_tests, program_name, test_name)

        # Write the output files for the test.
        for output_key in outputs.keys():
            output_path = os.path.join(instance.run_archive_instance_path, 'output_' + output_key + ".txt")
            self.write_output(output_path, outputs[output_key])

        # Create a dictionary for holding the fully made events.
        complete_events = {}
        # Create a dictionary for holding the paths to each of these events.
        event_paths = {}
        # For each event, make sure it has all of it's needed keys and if not, add them.
        for event_key in events.keys():
            # Copy the event so that the same event can be used for multiple different tests correctly.
            event_dic = copy.copy(events[event_key])
            file_name = 'Event_' + str(event_key) + '.txt'
            if 'app' not in event_dic.keys():
                event_dic['app'] = program_name
            if 'test' not in event_dic.keys():
                event_dic['test'] = test_name
            if 'rgt_system_log_tag' not in event_dic.keys():
                event_dic['rgt_system_log_tag'] = system
            if 'run_archive' not in event_dic.keys():
                event_dic['run_archive'] = instance.run_archive_instance_path
            if 'event_filename' not in event_dic.keys():
                event_dic['event_filename'] = file_name
            if 'event_time' not in event_dic.keys():
                event_dic['event_time'] = time
            if 'test_id' not in event_dic.keys():
                event_dic['test_id'] = instance_name
            # Set the path to the event.
            event_path = os.path.join(instance.status_instance_path, file_name)
            # Write the event file.
            self.write_event(event_path, event_dic)

            # Add the event to the dictionary.
            complete_events[event_key] = event_dic
            # Add the path to the dictionary.
            event_paths[event_key] = event_path
        # Set them as class variables.
        instance.complete_events = complete_events
        instance.event_paths = event_paths

        # Write the file that holds the exit status for the job.
        self.write_exit_value(job_id, exit_status)

        # Write the file that holds whether the job exists in LSF.
        self.write_in_queue_value(job_id, in_queue)

        return instance

    @staticmethod
    def create_rgt_status_line(harness_start, harness_uid, job_id, build_status, submit_status, check_status):
        """
        The rgt status line for the test.

        :param harness_start: When the test began.
        :param harness_uid: The uid for the test.
        :param job_id: The id in LSF for the test.
        :param build_status: The build status for the test.
        :param submit_status: The submit status for the test.
        :param check_status: The check status for the test.
        :return: A dictionary containing the input values.
        """
        return {'harness_start': harness_start, 'harness_uid': harness_uid, 'job_id': job_id,
                'build_status': build_status, 'submit_status': submit_status, 'check_status': check_status}

    @staticmethod
    def write_event(path_to_event, event_dic):
        """
        Write the event file.

        :param path_to_event: The path to where the event should be stored.
        :param event_dic: The dictionary for the event.
        """
        # Create the text for the event file.
        text = ""
        for key in event_dic.keys():
            text += "{key}={value} ".format(key=key, value=event_dic[key])

        # Write it to the file.
        with open(path_to_event, mode='w+') as f:
            f.write(text)

    def write_output(self, output_filename, text):
        """
        Write the output file.

        :param output_filename: The name of the ouput file.
        :param text: The text to write to the output.
        """
        with open(os.path.join(self.path_to_output_files, output_filename), "w+") as f:
            f.write(text)

    @staticmethod
    def write_rgt_status(path_to_rgt_status, harness_start, harness_uid, job_id,
                         build_status, submit_status, check_status):
        """
        Write a line in the rgt status file for this test. If the rgt status file already exists for a different
        instance, append to that file.

        :param path_to_rgt_status: Path to where the rgt status file is.
        :param harness_start: When the test began.
        :param harness_uid: The uid for the test.
        :param job_id: The id in LSF for the test.
        :param build_status: The build status for the test.
        :param submit_status: The submit status for the test.
        :param check_status: The check status for the test.
        """
        text = ""
        # Assume we will append to the file.
        mode = "a"
        # If it does not exist, add a header and change the mode.
        if not os.path.exists(path_to_rgt_status):
            text += "##################################\n" + \
                    "# Start time   Unique ID   Batch ID    Build Status    Submit Status   Check Status\n" + \
                    "##################################\n"
            mode = "w+"

        # Create the text line.
        text += "{harness_start} {harness_uid} {job_id} {build_status} {submit_status} {check_status}\n" \
            .format(harness_start=harness_start, harness_uid=harness_uid, job_id=job_id,
                    build_status=build_status, submit_status=submit_status, check_status=check_status)

        # Write it to the file.
        with open(path_to_rgt_status, mode=mode) as f:
            f.write(text)

    @staticmethod
    def make_directory(directory_path):
        """
        Create a directory if it does not yet exist.
        :param directory_path: The path to the directory.
        """
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

    def make_directories(self, program_name, test_name, instance_name, path_to_example_tests):
        """
        Make all directories for some test instance.

        :param program_name: The name of the program.
        :param test_name: The name of the test.
        :param instance_name: The harness_uid.
        :param path_to_example_tests: The path to where this directory stack should go.
        :returns: the path to the run_archive for the test, the path to the status directory for the test.
        """
        # Create the program directory.
        program_path = os.path.join(path_to_example_tests, program_name)
        self.make_directory(program_path)

        # Create the test directory.
        test_path = os.path.join(program_path, test_name)
        self.make_directory(test_path)

        # Create the status directory.
        status_path = os.path.join(test_path, 'Status')
        self.make_directory(status_path)
        # Create the run_archive directory.
        run_archive_path = os.path.join(test_path, 'Run_Archive')
        self.make_directory(run_archive_path)

        # Create the Status/instance directory.
        status_instance_path = os.path.join(status_path, instance_name)
        self.make_directory(status_instance_path)
        # Create the Run_Archive/instance directory.
        run_archive_instance_path = os.path.join(run_archive_path, instance_name)
        self.make_directory(run_archive_instance_path)

        return run_archive_instance_path, status_instance_path

    def replacement_lsf_exit_function(self, job_id):
        """
        A function for replacing how LSF is read. This means there is less reliance on what LSF is doing.

        :param job_id: The id for the test in LSF (or what it would have been).
        :return: The value read from some file.
        """
        # Path to where the file is.
        file_path = os.path.join(self.path_to_lsf_files, str(job_id) + '_exit_status.txt')
        # Get the exit value.
        with open(file_path, mode='r') as f:
            exit_value = f.read()

        # Send it back if there is one and if not, return None.
        if len(exit_value) == 0:
            return None
        else:
            return int(exit_value)

    def write_exit_value(self, job_id, value):
        """
        Write the exit value for some test.

        :param job_id: The id of the test in LSF.
        :param value: The value to be written.
        """
        # The path to where the exit value file will be stored.
        file_path = os.path.join(self.path_to_lsf_files, str(job_id) + '_exit_status.txt')
        # Write the value to the file.
        with open(file_path, mode='w+') as f:
            if value is None:
                f.write('')
            else:
                f.write(str(value))

    def replacement_in_queue_function(self, job_id):
        """
        A function for replacing how LSF is read. This means there is less reliance on what LSF is doing.

        :param job_id: The id for the test in LSF (or what it would have been).
        :return: The value read from some file.
        """
        # Path to where the file is.
        file_path = os.path.join(self.path_to_lsf_files, str(job_id) + '_in_queue_status.txt')
        # Get the exit value.
        with open(file_path, mode='r') as f:
            in_queue = f.read()

        # Send it back if there is one and if not, return None.
        if 'False' in in_queue:
            return False
        elif 'True' in in_queue:
            return True

    def write_in_queue_value(self, job_id, value):
        """
        Write the exit value for some test.

        :param job_id: The id of the test in LSF.
        :param value: The value to be written.
        """
        # The path to where the exit value file will be stored.
        file_path = os.path.join(self.path_to_lsf_files, str(job_id) + '_in_queue_status.txt')
        # Write the value to the file.
        with open(file_path, mode='w+') as f:
            if value is None:
                f.write('')
            else:
                f.write(str(value))

    @staticmethod
    def write_rgt_input(path_to_rgt_input, path_to_tests, program_name, test_name):
        """
        Write the line in the rgt_input for the test instance.

        :param path_to_rgt_input: The path to where the rgt input should be.
        :param path_to_tests: The path to where the tests are stored.
        :param program_name: The name of the program for the test.
        :param test_name: The name of the test.
        """
        # Assume the rgt input already exists.
        mode = 'a'
        text = ""
        # If not, add a header and change the mode.
        if not os.path.exists(path_to_rgt_input):
            mode = 'w+'
            text += "path_to_tests = " + path_to_tests + "\n"

        # Add the line.
        text += "test = " + program_name + " " + test_name + "\n"

        # Write to the file.
        with open(path_to_rgt_input, mode=mode) as f:
            f.write(text)


class TestUpdateDatabase(unittest.TestCase):
    """
    This class tests that updating the database works correctly.
    """
    def drop_tables(self):
        """
        Destroy all tables. This is useful for finding where a table might have become locked.
        """
        if self.verbose:
            print("Trying to drop every table.")
        tables = [self.test_event_table, self.test_table, self.event_table]
        for i in range(len(tables)):
            self.drop_table(tables[i])

    def drop_table(self, table):
        """
        Drop a table in the database.
        :param table: The name of the table to drop.
        """
        if self.verbose:
            print("Trying to drop " + str(table))
        db = self.connector.connect()
        cursor = db.cursor()
        # First delete the contents, then drop the table.
        delete_sql = "DELETE FROM `" + table + "`"
        drop_sql = "DROP TABLE `" + table + "`"
        for i in range(2):
            sql_list = [delete_sql, drop_sql]
            sql = sql_list[i]
            try:
                cursor.execute(sql)
            except Exception as e:
                raise type(e)(str(e) + " Error running '" + sql + "'")
        db.commit()
        db.close()

    def show_table(self, table):
        """
        Show the contents of some table in the database.
        :param table: The table to show.
        """
        if self.verbose:
            print("Trying to show " + str(table))
        # Connect to the database.
        db = self.connector.connect()
        cursor = db.cursor()
        # Select everything from the table.
        sql = "SELECT * FROM " + table
        if self.verbose:
            print("Running " + sql)
        try:
            cursor.execute(sql)
        except Exception as e:
            raise type(e)(str(e) + " Error running '" + sql + "'")
        print(cursor.fetchall())
        # Close the connection.
        db.commit()
        db.close()

    def init_directories(self):
        """
        Initialize all directories to where files will be stored.
        :return:
        """
        self.IC.make_directory(self.IC.path_to_lsf_files)
        self.IC.make_directory(self.IC.path_to_output_files)
        self.IC.make_directory(self.IC.path_to_example_tests)

    def remove_directories(self):
        """
        Remove all directories previously made for holding test information. This does not remove the top directory.
        """
        # List everything in the directory.
        for f in os.listdir(self.IC.path_to_inputs):
            file_path = os.path.join(self.IC.path_to_inputs, f)

            # Unlink if it is a file. Otherwise remove the tree.
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def setUp(self):
        """
        Each time a new test is run. Drop old tables/directories and create new tables to act on.
        """
        self.verbose = False

        # Set the path to the drop tables file.
        drop_tables_path = os.path.join(os.path.dirname(__file__), 'drop_test_tables.sql')
        if self.verbose:
            print("Removing tables.")
        # Only try running for at most 10 seconds. Any longer and the most likely problem is that a table was locked.
        try:
            with time_limit(10):
                create_database.execute_sql_file(self.connector, drop_tables_path)
        except TimeoutException as e:
            print("TIMEOUT: I timed out trying to drop tables. This is most likely because a table was locked.")
        # Remove all directories created.
        self.remove_directories()

        # Create the new tables and what not.
        # Set the names of each of the tables.
        self.test_table = 'test_rgt_test'
        self.test_event_table = 'test_rgt_test_event'
        self.event_table = 'test_rgt_event'
        self.check_table = 'test_rgt_check'
        self.IC = InstanceCreator()

        # Get the config for the database.
        database_conf = config_functions.get_config()['DATABASE']
        # Initialize a connector to the database.
        self.connector = connect_database.DatabaseConnector(database_conf)

        # Set the path to the file for creating the test tables.
        create_tables_path = os.path.join(os.path.dirname(__file__), 'create_test_tables.sql')
        # Create the tables.
        create_database.execute_sql_file(self.connector, create_tables_path)

        # Initialize the directories for the test.
        self.init_directories()

    def init_update_database(self, rgt_input_path=''):
        """
        Initialize the UpdateDatabase class. Everything should be setup before initializing the class.

        :param rgt_input_path: The path to the rgt input file.
        """
        self.UD = update_database.UpdateDatabase(self.connector, rgt_input_path, test_table=self.test_table,
                                                 test_event_table=self.test_event_table, event_table=self.event_table,
                                                 check_table=self.check_table,
                                                 replacement_lsf_exit_function=self.IC.replacement_lsf_exit_function,
                                                 replacement_in_queue_function=self.IC.replacement_in_queue_function)

    def insert_event(self, event_uid, event_name='test'):
        """
        Insert an event into the event table.

        :param event_uid: The uid for the event.
        :param event_name: The name of the event.
        """
        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()

        # Insert the uid, name combo into the event table.
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, '{event_name}') ON DUPLICATE KEY " \
              "UPDATE event_name='{event_name}'"
        sql = sql.format(table=self.event_table, event_uid=event_uid, event_name=event_name)
        # Try to execute.
        try:
            cursor.execute(sql)
        except Exception as e:
            db.rollback()
            db.close()
            raise e
        else:
            db.commit()
        db.close()

    def in_table(self, table_name, **kwargs):
        """
        Test if some set of values is in the table.

        :param table_name: The name of the table to search.
        :param kwargs: The field, value pairs to search for.
        :return: Whether or not there was an entry with the specified values.
        """
        # Select whether the entry exists.
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE".format(table=table_name)
        # Get the list of fields in the dictionary.
        key_list = list(kwargs.keys())
        for i in range(len(kwargs)):
            # Get the key and value.
            key = key_list[i]
            val = kwargs[key]

            # Depending on the type of the value, search for it in different ways.
            if type(val) is int:
                val_string = str(val)
            elif type(val) is str:
                val_string = "'" + val + "'"
            elif type(val) is bool:
                val_string = str(val).upper()

            # Add the necessary text to the sql.
            sql += " " + key + " = " + val_string
            # If there is another key, put an AND in.
            if i < len(kwargs) - 1:
                sql += " AND"

        # Finish off the search sql.
        sql += ")"

        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Run the command.
        cursor.execute(sql)
        db.commit()
        # Return the boolean value of whether it existed or not.
        return bool(cursor.fetchone()[0])

    def test_get_event_id(self):
        """
        Test whether the get_event_id function works.
        """
        # Create the event.
        event_uid = 0
        self.insert_event(event_uid, 'test')

        # Test that the correct event id is returned.
        self.init_update_database()
        event_id = self.UD.get_event_id(event_uid)
        self.assertEqual(1, event_id)

        # Try it for another event.
        event_uid = 1
        self.insert_event(event_uid, 'test')
        event_id = self.UD.get_event_id(event_uid)
        self.assertEqual(2, event_id)

    def test_get_event_uid(self):
        """
        Test whether the get_event_uid function works.
        """
        # Insert multiple events.
        self.insert_event(0)
        self.insert_event(1)
        self.insert_event(2)

        self.init_update_database()

        # Test that the event uid can be parsed from an event dictionary.
        event_dic = {'event_filename': 'Event_0.txt'}
        event_uid = self.UD.get_event_uid(event_dic)
        self.assertEqual(event_uid, 0)

        event_dic = {'event_filename': 'Event_3.txt'}
        event_uid = self.UD.get_event_uid(event_dic)
        self.assertIsNone(event_uid)

    def test_insert_parsed_event_into_event_table(self):
        """
        Test whether the insert_parsed_event_into_event_table function works.
        """
        # Insert a new test into the test table. This is because of the unique key is needed.
        # Initialize a database connection.
        db = self.connector.connect()
        with db.cursor() as cursor:
            sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
                  "application, testname, system, next_harness_uid, done)" \
                  " VALUES ('2', '0000-00-00', 'path', 'app', 'test', 'sys', 1, FALSE)"
            sql = sql.format(table=self.test_table)
            cursor.execute(sql)
        db.commit()
        db.close()

        # Insert a new event into the event table. This is once agian because the unique key is needed.
        self.insert_event(1)

        self.init_update_database()

        # Insert a parsed event into the table.
        self.UD.insert_parsed_event_into_event_table(1, 1, '0000-00-01')

        # Test that the correct stuff is in the table.
        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1}))
        self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 1}))

    def test_get_exit_status(self):
        """
        Test whether the get_exit_status function works.
        """
        # Write the exit value for some job.
        job_id_0 = 0
        exit_status_0 = 0
        self.IC.write_exit_value(job_id_0, exit_status_0)

        # Write the exit value for some job.
        job_id_1 = 1
        exit_status_1 = 1
        self.IC.write_exit_value(job_id_1, exit_status_1)

        self.init_update_database()

        # Assert that the correct exit values are returned.
        self.assertEqual(exit_status_0, self.UD.get_exit_status(job_id_0))
        self.assertEqual(exit_status_1, self.UD.get_exit_status(job_id_1))

    def test_output_text(self):
        """
        Test whether the output_text function works.
        """
        self.init_update_database()

        # Assert that there is no output found for a bad path and output name.
        self.assertIsNone(self.UD.output_text('path', 'bad_output'))

        # Write an example output file.
        output_type = 'build'
        output_filename = 'output_' + output_type + '.txt'
        text = 'Example output text.'
        self.IC.write_output(output_filename, text)

        # Test that it is found.
        self.assertEqual(text, self.UD.output_text(self.IC.path_to_output_files, output_type))

    def test_get_update_fields_bad_rgt(self):
        """
        Test whether the get_update_fields function works for a bad rgt line.
        """
        # Try to parse a bad rgt line with incorrect fields.
        bad_rgt_line = {'incorrect': 'length'}
        self.init_update_database()

        fields = self.UD.get_update_fields(bad_rgt_line, {})
        self.assertEqual(len(fields.keys()), 0)

    def test_get_update_fields_good_building(self):
        """
        Test that the correct update fields are found for a test that is building.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 10
        build_status = '0'
        submit_status = '***'
        check_status = '***'
        build_output_text = 'building . . .'
        submit_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None
        in_queue = False

        # Create a parsed rgt status line.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Create a test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        self.init_update_database()

        # Get the fields that would be updated.
        update_fields = self.UD.get_update_fields(rgt_line, instance.complete_events['0']['run_archive'])

        # There should be keys for all things that can change while a test is running.
        # No exit status key because it is set to null and no status problems.
        # No submit or check status because they are both not integers.
        # Expect output build and submit because they will both have files.
        expected_result = {'job_id': job_id, 'build_status': int(build_status),
                           'output_build': build_output_text, 'output_submit': submit_output_text,
                           'done': False}
        for key in expected_result.keys():
            self.assertIn(key, update_fields.keys())

            self.assertEqual(expected_result[key], update_fields[key])

        # Check that there are no keys that should not be in there.
        for key in update_fields.keys():
            self.assertIn(key, expected_result.keys())

    def test_get_update_fields_good_exited(self):
        """
        Test that the correct update fields are found for a test that has exited.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 2
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . . \nAll done'
        submit_output_text = 'submitting . . .\n Submitted'
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = 140
        in_queue = False

        # Get a parsed rgt status line.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Create the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        self.init_update_database()

        update_fields = self.UD.get_update_fields(rgt_line, instance.complete_events['0']['run_archive'])

        # There should be keys for all things that can change while a test is running.
        # Expect exit status since it is set.
        # No check status because it is not an int.
        # Expect output build and submit because they will both have files.
        expected_result = {'job_id': job_id, 'build_status': int(build_status), 'submit_status': int(submit_status),
                           'output_build': build_output_text, 'output_submit': submit_output_text,
                           'lsf_exit_status': exit_status, 'done': True}
        for key in expected_result.keys():
            self.assertIn(key, list(update_fields.keys()))

            self.assertEqual(expected_result[key], update_fields[key])

        # Check that there are no keys that should not be in there.
        for key in update_fields.keys():
            self.assertIn(key, expected_result.keys())

    def test_get_update_sql(self):
        """
        Test that get_update_sql works.
        """
        # Set the update fields.
        update_fields = {'int_1': 10, 'int_2': 20, 'str_1': 'one', 'str_2': 'two'}
        test_id = 100

        self.init_update_database()

        # Create the update sql.
        sql = self.UD.get_update_sql(update_fields, test_id)

        # Assert that the correct sql is there.
        self.assertIn('UPDATE test_rgt_test', sql)
        self.assertIn('int_1 = 10', sql)
        self.assertIn('int_2 = 20', sql)
        self.assertIn("str_1 = 'one'", sql)
        self.assertIn("str_2 = 'two'", sql)
        self.assertIn('WHERE', sql)
        self.assertIn('test_id = ' + str(test_id), sql)

    def test_update_test_table(self):
        """
        Test that the test table can be updated for some test.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-00'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None
        in_queue = False

        # Create an rgt status line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize a test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Insert the test into the test table.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " + \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ('{harness_uid}', '{harness_start}', '{harness_tld}', " + \
              "'{application}', '{testname}', '{system}', '{next_harness_uid}', {done})"

        sql = sql.format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                         application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)

        # Execute and close the database.
        cursor.execute(sql)
        db.commit()
        db.close()
        # Update the test table with the test instance.
        self.init_update_database()
        self.UD.update_test_table(1, instance.complete_events['0']['run_archive'], rgt_line)

        # Assert that the expected result is in the test table.
        expected_vals = {'harness_uid': harness_uid, 'output_build': outputs['build'],
                         'output_submit': outputs['submit'], 'output_check': outputs['check'],
                         'job_id': job_id, 'build_status': build_status, 'submit_status': submit_status,
                         'system': system}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

    def test_get_add_fields(self):
        """
        Test that the correct fields can be found when adding a test.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 2
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . . \nAll done'
        submit_output_text = 'submitting . . .\n Submitted'
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = 140
        in_queue = False

        # Create an rgt status line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize a test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        self.init_update_database()

        # Get the add fields.
        job_path = instance.status_instance_path
        add_fields = self.UD.get_add_fields(rgt_line, instance.complete_events['0'], job_path)

        # There should be keys for all things that can not change while a test is running.
        expected_result = {'harness_uid': harness_uid, 'harness_start': time, 'harness_tld': job_path,
                           'application': program_name, 'testname': test_name, 'system': system,
                           'next_harness_uid': harness_uid}
        for key in expected_result.keys():
            self.assertIn(key, add_fields.keys())

            self.assertEqual(expected_result[key], add_fields[key])

        # Check that there are no keys that should not be in there.
        for key in add_fields.keys():
            self.assertIn(key, expected_result.keys())

    def test_get_add_sql(self):
        """
        Test that the correct sql can be made for adding a test.
        """
        # Set the fields to add.
        add_fields = {'int_1': 10, 'int_2': 20, 'str_1': 'one', 'str_2': 'two'}

        self.init_update_database()

        # Get the sql.
        sql = self.UD.get_add_sql(add_fields)

        # Assert that it has the correct stuff.
        self.assertIn('INSERT INTO test_rgt_test', sql)
        self.assertIn('int_1', sql)
        self.assertIn('int_2', sql)
        self.assertIn('str_1', sql)
        self.assertIn('str_2', sql)
        self.assertIn('10', sql)
        self.assertIn('20', sql)
        self.assertIn("'one'", sql)
        self.assertIn("'two'", sql)

    def test_add_to_test_table(self):
        """
        Test that a test can be added to the test table.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None
        in_queue = False

        # Initialize the rgt line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        harness_tld = instance.status_instance_path

        # Add the test to the test table.
        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0'], rgt_line, harness_tld)

        # Make sure the expected result is in the table.
        expected_vals = {'harness_uid': harness_uid, 'output_build': outputs['build'],
                         'output_submit': outputs['submit'], 'output_check': outputs['check'],
                         'job_id': job_id, 'build_status': build_status, 'submit_status': submit_status,
                         'system': system}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

    def test_in_event_table(self):
        """
        Test whether an event can be found in the test event table.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uid = '0'
        events = {event_uid: {}}
        exit_status = None
        in_queue = False

        # Initialize the rgt line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        harness_tld = instance.status_instance_path

        # Add the test to the test table.
        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0'], rgt_line, harness_tld)

        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Insert the event into the event table.
        self.insert_event(event_uid)
        # Insert the test, event pair.
        sql = "INSERT INTO {table} (test_id, event_id, event_time) " \
              "VALUES ({test_id}, {event_id}, {event_time})"\
              .format(table=self.test_event_table, test_id=1, event_id=1, event_time=time)
        cursor.execute(sql)
        db.commit()

        # Assert that test_instance 1 has an event with id 1. These are NOT the uids.
        self.assertTrue(self.UD.in_event_table(1, 1))

    def test_insert_into_event_table(self):
        """
        Test if the test, event pair can be added to the test event table.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uid = '0'
        events = {event_uid: {}}
        exit_status = None
        in_queue = False

        # Initialize the rgt line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        harness_tld = instance.status_instance_path

        # Insert the event.
        self.insert_event(event_uid)

        # Add the test to the test table.
        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0'], rgt_line, harness_tld)

        # Assert that the pair is not yet in the test event table.
        self.assertFalse(self.UD.in_event_table(1, 1))
        # Insert the pair.
        self.UD.insert_into_event_table(1, instance.event_paths['0'])
        # Assert that the pair is now in the test event table.
        self.assertTrue(self.UD.in_event_table(1, 1))

    def test_update_test_event_table(self):
        """
        Test that the test event table can be updated for one test.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uids = ['0', '1']
        events = {event_uids[0]: {}, event_uids[1]: {}}
        exit_status = None
        in_queue = False

        # Insert all of the events.
        for uid in event_uids:
            self.insert_event(uid)

        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        status_path = instance.status_instance_path

        # Get the paths to all of this tests events.
        self.init_update_database()
        event_paths = self.UD.get_event_paths(status_path)

        expected_paths = [instance.event_paths[key] for key in instance.event_paths.keys()]

        # Make sure all of the event paths exist.
        for expected_path in expected_paths:
            self.assertIn(expected_path, event_paths)

        for event_path in event_paths:
            self.assertIn(event_path, expected_paths)

        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Insert the test into the test table.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " + \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ('{harness_uid}', '{harness_start}', '{harness_tld}', " + \
              "'{application}', '{testname}', '{system}', '{next_harness_uid}', {done})"

        sql = sql.format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                         application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)

        # Execute and close the database.
        cursor.execute(sql)
        db.commit()
        db.close()

        # Update the table.
        self.UD.update_test_event_table(event_paths, 1)

        # Check that each event is in the table.
        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 1}))
        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 2}))

    def test_add_test_instance(self):
        """
        Test that a test can be added correctly.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uids = ['0', '1']
        events = {event_uids[0]: {}, event_uids[1]: {}}
        exit_status = None
        in_queue = False

        # Insert the events for the test.
        self.insert_event(event_uids[0])
        self.insert_event(event_uids[1])

        # Initialize the rgt line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        harness_tld = instance.status_instance_path

        # Add the test.
        self.init_update_database()
        self.UD.add_test_instance(harness_tld, rgt_line)

        # Make sure the test is in the table.
        expected_vals = {'harness_uid': harness_uid, 'job_id': job_id, 'build_status': build_status,
                         'submit_status': submit_status}
        self.assertTrue(self.in_table(self.test_table, **expected_vals), msg=str(expected_vals))

        # Check that the events are in the table.
        expected_event_vals = {'0': {'event_id': 1}, '1': {'event_id': 2}}

        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['0']))
        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['1']))

        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 1}))
        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 2}))

    # TODO: Simplify test instance introduction.
    def test_update_test_instance(self):
        """
        Test that a test can be updated.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uids = ['0', '1']
        events = {event_uids[0]: {}, event_uids[1]: {}}
        exit_status = None
        in_queue = False

        # Add the events.
        for uid in event_uids:
            self.insert_event(uid)

        # Initialize the rgt line for the test.
        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        # Initialize the test instance.
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status, in_queue)

        harness_tld = instance.status_instance_path

        # Insert the test.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ('{harness_uid}', '{harness_start}', '{harness_tld}', " \
              "'{application}', '{testname}', '{system}', '{next_harness_uid}', {done})"
        
        sql = sql.format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                         application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)
        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        db.close()

        # Update the test.
        self.init_update_database()
        self.UD.update_test_instance(1, harness_tld, rgt_line)

        # Check that the expected line is in the table.
        expected_vals = {'harness_uid': harness_uid, 'job_id': job_id, 'build_status': build_status,
                         'submit_status': submit_status, 'output_build': build_output_text}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

        # Check that the expected events are in the table.
        expected_event_vals = {'0': {'event_id': 1}, '1': {'event_id': 2}}

        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['0']))
        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['1']))

        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 1}))
        self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 1, 'event_id': 2}))

    def test_get_job_tuple(self):
        """
        Test that the tuple for some job can be found.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uid = 'instance'
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        event_uids = ['0', '1']
        events = {event_uids[0]: {}, event_uids[1]: {}}
        exit_status = None
        in_queue = False

        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Insert the test.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ('{harness_uid}', '{harness_start}', '{harness_tld}', " \
              "'{application}', '{testname}', '{system}', '{next_harness_uid}', {done})" 

        sql = sql.format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                         application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)
        # Execute and close the connection.
        cursor.execute(sql)
        db.commit()
        db.close()

        # Get the job tuple.
        self.init_update_database()
        job_tuple = self.UD.get_job_tuple(harness_uid)
        # Assert that it contains the correct information.
        self.assertEqual(job_tuple[0], 1)
        self.assertEqual(job_tuple[1], False)

    def test_update_test_instances(self):
        """
        Test that multiple test instances can be updated/added.
        """
        # Initialize test variables.
        program_name = 'program'
        test_name = 'test'
        time = '0000-00-01'
        harness_uids = ['instance_A', 'instance_B']
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None
        in_queue = False

        # Initialize the test instance.
        instance_A = self.IC.create_test_instance(program_name, test_name, harness_uids[0], time, job_id, build_status,
                                                  submit_status, check_status, outputs, system, events, exit_status, in_queue)
        # Initialize the test instance.
        instance_B = self.IC.create_test_instance(program_name, test_name, harness_uids[1], time, job_id, build_status,
                                                  submit_status, check_status, outputs, system, events, exit_status, in_queue)

        # Try with one already in database and the other just needing to be updated.
        self.insert_event(0)

        # Insert one of the instances.
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ('{harness_uid}', '{harness_start}', '{harness_tld}', " \
              "'{application}', '{testname}', '{system}', '{next_harness_uid}', {done})"
        sql = sql.format(table=self.test_table, harness_uid=harness_uids[0], harness_start=time, harness_tld='path',
                         application=program_name, testname=test_name, system=system, next_harness_uid=harness_uids[0],
                         done=False)
        # Initialize a database connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Execute and close the connection.
        cursor.execute(sql)
        db.commit()
        db.close()

        # Assert that the full tests are not yet in the database.
        self.assertFalse(self.in_table(self.test_table, **{'harness_uid': harness_uids[0], 'build_status': build_status}))
        self.assertFalse(self.in_table(self.test_table, **{'harness_uid': harness_uids[1]}))
        self.assertFalse(self.in_table(self.test_event_table, **{'event_id': 0}))

        # Add the tests.
        self.init_update_database()
        self.UD.update_test_instances(os.path.dirname(instance_A.status_instance_path))

        # Assert that the full tests are now in the database.
        self.assertTrue(self.in_table(self.test_table, **{'harness_uid': harness_uids[0], 'build_status': build_status,
                                                          'output_build': build_output_text}))
        self.assertTrue(self.in_table(self.test_table, **{'harness_uid': harness_uids[1],
                                                          'output_build': build_output_text}))
        self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 1, 'test_id': 1}))
        self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 1, 'test_id': 2}))

    def test_update_tests(self):
        """
        Test that many instances can be added/updated from the rgt input file.
        :return:
        """
        # Initialize test variables.
        program_names = ['program_1', 'program_2']
        test_names = ['test_alpha', 'test_beta']
        time = '0000-00-01'
        harness_uids = ['instance_A', 'instance_B', 'instance_C']
        job_id = 11
        build_status = '0'
        submit_status = '0'
        check_status = '***'
        build_output_text = 'building . . .\nAll done'
        submit_output_text = 'submitting . . .\nAll done'
        check_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text, 'check': check_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None
        in_queue = False

        # Create many test instances.
        instance_count = 0
        new_uids = []
        for program_name in program_names:
            for test_name in test_names:
                for harness_uid in harness_uids:
                    if random() > 0.5 or instance_count == 0:
                        new_uid = program_name + '_' + test_name + '_' + harness_uid

                        # Initialize the test instance.
                        instance = self.IC.create_test_instance(program_name, test_name, new_uid, time, job_id,
                                                                build_status, submit_status, check_status, outputs,
                                                                system, events, exit_status, in_queue)
                        instance_count += 1
                        new_uids.append(new_uid)

        # Try with one already in database and the other just needing to be updated.
        self.insert_event(0)

        # Check the each uid is not yet in the table.
        for uid in new_uids:
            self.assertFalse(self.in_table(self.test_table, **{'harness_uid': uid}))

        # Update all of the tests.
        self.init_update_database(self.IC.path_to_rgt_input)
        self.UD.update_tests()

        # Check that they are now in the table.
        for uid in new_uids:
            self.assertTrue(self.in_table(self.test_table, **{'harness_uid': uid, 'done': False}))

