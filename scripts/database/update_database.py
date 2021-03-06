"""
This file updates the database using any new things in the rgt.input and all things currently in the database
that are not yet done.
"""
import os
from scripts import job_status
import warnings
from scripts import parse_file
from scripts import test_status


def get_event_types(connector, event_table):
    """
    Get all the types of events that a test instance can output.

    :param connector: The connector to the database.
    :param event_table: The name of the event table.
    :return: A list of tuples corresponding to the event types.
    """
    database = connector.connect()
    cursor = database.cursor()
    sql = "SELECT (event_uid) FROM {table}".format(table=event_table)

    cursor.execute(sql)
    database.commit()
    database.close()
    event_types = cursor.fetchall()
    event_types = [event_type[0] for event_type in event_types]

    return event_types


class PermissionWarning(UserWarning):
    pass


def execute_sql(sql, db):
    """
    Execute some sql on the database. Only works when not expecting a response.

    :param sql: SQL to execute.
    :param db: Database to execute on.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings('error')

        cursor = db.cursor()
        try:
            # Execute the command.
            cursor.execute(sql)
        except Exception as e:
            # Throw a nice warning if there was a problem.
            warnings.warn(str(e) + '\n' + repr(sql))
        else:
            # Commit it to the database.
            db.commit()


class UpdateDatabase:
    """
    This class takes care of running all necessary functions for updating the database. It does not repeat.
    """
    def __init__(self, connector, rgt_input_path, test_table='rgt_test', test_event_table='rgt_test_event',
                 event_table='rgt_event', check_table='rgt_check',
                 verbose=False, replacement_lsf_exit_function=None, replacement_in_queue_function=None):
        """
        Constructor for updating the database.

        :param connector: DatabaseConnector for connection so some database.
        :param rgt_input_path: The path to the rgt_input file.
        :param test_table: The name of the table where tests are stored.
        :param test_event_table: The name of the table where test, event pairs are stored.
        :param event_table: The name of the table where event types are stored.
        :param verbose: Whether to print out what is currently happening while updating.
        """
        # Set the connections to the database.
        self.connector = connector

        # Set the path to where new tests come from.
        self.rgt_input_path = rgt_input_path

        # The names of the different tables to use. This is useful when doing unit tests so that the actual tables
        # are not getting messed up with our tomfoolery.
        self.test_table = test_table
        self.test_event_table = test_event_table
        self.event_table = event_table
        self.check_table = check_table

        # Set the types of events we are prepared to handle.
        self.event_types = get_event_types(self.connector, self.event_table)
        # The fields within an rgt_status.txt file.
        self.rgt_fields = ['harness_start', 'harness_uid', 'job_id', 'build_status', 'submit_status', 'check_status']

        # The possible output files that we are prepared to handle. They will go like "*_output.txt".
        self.possible_outputs = ['build', 'submit', 'check', 'report']

        self.verbose = verbose

        # This is used for testing so that fake jobs can be tested instead of getting stuff from LSF.
        self.lsf_exit_function = None
        if replacement_lsf_exit_function is not None:
            self.lsf_exit_function = replacement_lsf_exit_function
        self.in_queue_function = None
        if replacement_in_queue_function is not None:
            self.in_queue_function = replacement_in_queue_function

    def update_tests(self):
        """
        Add all tests from the rgt.input file that are not yet in the database.

        :return:
        """
        # Get the test directories from the file.
        test_directories, harness_tld = self.get_test_dirs_from_rgt()

        # For each test directory, add any new UIDs from that test.
        for test_dir in test_directories:
            self.update_test_instances(test_dir, harness_tld)

    def get_test_dirs_from_rgt(self):
        """
        Get the directories to each test. Each directory is appended with '/Status/' since we
        do not need any info from the directory above.

        :return: A list of test directories. The path to the tests.
        """
        # Create the parser.
        parser = parse_file.ParseRGTInput()
        # Get the path to tests and the list of tests.
        path_to_tests, test_list = parser.parse_file(self.rgt_input_path)
        # Get the test directories.
        test_directories = test_status.get_test_directories(path_to_tests, test_list, append_dirs='Status')
        return test_directories, path_to_tests

    def update_test_instances(self, test_path, harness_tld):
        """
        Add or update all uids for some test.

        :param test_path: Path to test ending in /Status/. This is the path just before
        entering any actual test instance.
        :param harness_tld: Path in rgt input.
        """
        if not os.path.exists(test_path):
            warnings.warn("Could not find path to this test.\n" + test_path)
            return

        # Create the path.
        self.rgt_status_path = os.path.join(test_path, 'rgt_status.txt')
        # Create the parser.
        rgt_parser = parse_file.ParseRGTStatus()
        # Get the dictionaries for each line in the status file.
        rgt_status_lines = rgt_parser.parse_file(self.rgt_status_path)

        # For each line in the file, add it to the table if it is new.
        for rgt_status_line in rgt_status_lines:
            # Get the uid for the test.
            harness_uid = rgt_status_line['harness_uid']

            job_tuple = self.get_job_tuple(harness_uid)

            path_to_instance = os.path.join(test_path, harness_uid)
            # Test if test instance exists in database. The job tuple is none if there was no match.
            if job_tuple is None:
                # If it does not, add it.
                self.add_test_instance(path_to_instance, rgt_status_line, harness_tld)
            # If in table but not done, update.
            elif not bool(job_tuple[1]):
                test_id = job_tuple[0]
                self.update_test_instance(test_id, path_to_instance, rgt_status_line)

    def get_job_tuple(self, harness_uid):
        """
        Get the test id and done status for some test instance.

        :param harness_uid: The uid of the instance to search for.
        :return: A tuple containing it's id and done status.
        """
        # Connect to the database.
        db = self.connector.connect()
        cursor = db.cursor()
        # Select the test_id and done status from the test table for this test instance..
        sql = "SELECT test_id, done FROM {table} WHERE harness_uid = '{harness_uid}'"
        sql = sql.format(table=self.test_table, harness_uid=harness_uid)
        # Execute and close the connection.
        cursor.execute(sql)
        db.commit()
        db.close()
        # Get the result.
        result = cursor.fetchone()
        return result

    def update_test_instance(self, test_id, path_to_instance, rgt_status_line):
        """
        Update a certain job entry.

        :param test_id: The id of the test in the database.
        :param path_to_instance: The path to where the test is stored.
        :param rgt_status_line: The line from the rgt_status file that corresponds to this test.
        :return:
        """
        # Get the paths to all events for this instance.
        event_paths = self.get_event_paths(path_to_instance)
        # Update the test event table with all of these events.
        self.update_test_event_table(event_paths, test_id)

        # If there is at least one event, get the path to where outputs are stored.
        if len(event_paths) != 0:
            event_path = event_paths[0]

            parser = parse_file.ParseEvent()
            parsed_event = parser.parse_file(event_path)
            output_path = parsed_event['run_archive']
            build_output_path = parsed_event['build_directory']
        else:
            output_path = None
            build_output_path = None
        # Insert new information into the main table.
        self.update_test_table(test_id, output_path, build_output_path, rgt_status_line)

    def add_test_instance(self, path_to_instance, rgt_status_line, harness_tld):
        """
        Add a test instance to the test table.

        :param path_to_instance: The path to where this instances events are stored.
        :param rgt_status_line: The line in the rgt status file that has already been parsed.
        :param harness_tld: The path in the rgt input.
        """
        # Get all event paths for this instance.
        event_paths = self.get_event_paths(path_to_instance)
        # If there are no events for this test, we do not have enough information to add it.
        if len(event_paths) == 0:
            warnings.warn("I can't find any events for this path and thus I do not have enough information to add\n" +
                          "this test.")
            return

        # Add the instance to the test table.
        event_path = event_paths[0]
        self.add_to_test_table(event_paths[0], rgt_status_line, harness_tld)

        # Parse the first event and get the uid and test_id.
        parser = parse_file.ParseEvent()
        parsed_event = parser.parse_file(event_path)
        harness_uid = parsed_event['test_id']
        test_id = self.get_test_id(harness_uid)
        # Update the test event table with all the events for this instance so far.
        self.update_test_event_table(event_paths, test_id)

    def get_event_paths(self, test_instance_status_path):
        """
        Get the paths to all events for some test instance.

        :param test_instance_status_path: The path to where the test instance is stored.
        :return: A list containing the paths to all events for that test.
        """
        if self.verbose:
            print("Getting events in " + str(test_instance_status_path) + ".")
        # Setup a list for holding the events.
        events = []
        # Get all immediate subfiles.
        for file in os.listdir(test_instance_status_path):
            # Filter to only get Events.
            if 'Event_' in file:
                # Check that the event is one that we are prepared to handle.
                for possible_event in self.event_types:
                    if str(possible_event) in file:
                        events.append(os.path.join(test_instance_status_path, file))
                        break
                # If it is not, give a warning that we are skipping it.
                else:
                    warnings.warn("I don't understand this event file. It is a code that I am not prepared to handle.\n"
                                  + os.path.join(test_instance_status_path, file))
        # Return file paths.
        return events

    def update_test_event_table(self, event_paths, test_id):
        """
        Update the test event table for some test by adding all the new events for it.

        :param event_paths: A list containing all the paths to all of some tests events.
        :param test_id: The id of the test in the database.
        """
        # Get a list of all events for this test instance. We sort them so that we can check the last test for the
        # lsf exit status.
        sorted_event_paths = sorted(event_paths)
        if self.verbose:
            if len(sorted_event_paths) == 1:
                print("Found 1 event. The path is " + str(sorted_event_paths) + ".")
            else:
                print("Found " + str(len(sorted_event_paths)) + " events."
                      " The paths are " + str(sorted_event_paths) + ".")
        # If there are events, start updating.
        if len(sorted_event_paths) != 0:
            # For each event, insert it into the event table connected to the correct event.
            for j in range(len(sorted_event_paths)):
                event_path = sorted_event_paths[j]
                self.insert_into_event_table(test_id, event_path)

    def insert_into_event_table(self, test_id, event_path):
        """
        Insert some event into the event table.

        :param test_id: The id of the test that this event is for.
        :param event_path: The path to the event file.
        :return:
        """
        # Parse the important info from the event file.
        parser = parse_file.ParseEvent()
        # Get the dictionary for the event.
        event_dic = parser.parse_file(event_path)
        # Get the events uid.
        event_uid = self.get_event_uid(event_dic)

        if event_uid is None:
            warnings.warn("Could not find the event that matches this file. " + event_path)
            return

        # Get the id of the event from the 'rgt_event' table.
        event_id = self.get_event_id(event_uid)

        # If it does not already exist in the table, put it in.
        if not self.in_event_table(test_id, event_id):
            # Get time when event occured.
            event_time = event_dic['event_time'].replace('T', ' ')

            # Enter it into the 'rgt_test_event' table.
            self.insert_parsed_event_into_event_table(test_id, event_id, event_time)

    def in_event_table(self, test_id, event_id):
        """
        Test if some event already exists in the table.

        :param test_id: The id that this event is connected to.
        :param event_id: The id of the event to check. Each event_id only happens once.
        :return: Whether the event already existed.
        """
        db = self.connector.connect()
        # Create a cursor for executing on the database.
        cursor = db.cursor()
        # Test if the test, event combo exists in the table.
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE test_id = {test_id} AND event_id = {event_id})"\
              .format(table=self.test_event_table, test_id=test_id, event_id=event_id)

        # Execute the command.
        cursor.execute(sql)
        db.commit()
        db.close()
        # Return whether or not it was in the table.
        in_table = bool(cursor.fetchone()[0])
        return in_table

    def insert_parsed_event_into_event_table(self, test_id, event_id, event_time):
        """
        Insert an event file after splitting into the relevant information.

        :param test_id: The id of the test that this event is for.
        :param event_id: The id of the event.
        :param event_time: When the event occurred.
        :return:
        """
        db = self.connector.connect()
        # Insert the necessary info into the table.
        sql = "INSERT INTO {table} (test_id, event_id, event_time) " \
              "VALUES ({test_id}, {event_id}, '{event_time}')" \
            .format(table=self.test_event_table, test_id=test_id, event_id=event_id, event_time=event_time)

        execute_sql(sql, db)

        db.close()

    def add_to_test_table(self, event_path, rgt_status_line, harness_tld):
        """
        Add a test to the test table.

        :param event_path: The path to some event for that test. This is needed since not all the necessary information
        is stored in the rgt_status file.
        :param rgt_status_line: The parsed line in the rgt status file for this test.
        :param harness_tld: The path to where this tests events are stored.
        """
        # Create parser for parsing event file.
        parser = parse_file.ParseEvent()
        # Get dictionary for the event.
        event_dic = parser.parse_file(event_path)
        # Get some fields to update that change based on time.
        update_fields = self.get_update_fields(rgt_status_line, event_dic['run_archive'], event_dic['build_directory'])
        # Get fields to update that are constant once the instance has been created.
        add_fields = self.get_add_fields(rgt_status_line, event_dic, harness_tld)

        # Concatenate the add fields and the update fields.
        all_fields = {**add_fields, **update_fields}

        # Get the sql code for inserting the values into the table.
        sql = self.get_add_sql(all_fields)
        db = self.connector.connect()

        execute_sql(sql, db)

        db.close()

    def get_add_sql(self, add_fields):
        """
        Get the sql needed to add a test to the test table.

        :param add_fields: The field, value combinations for the test. This is a dictionary.
        :return: The necessary sql.
        """
        # Insert into table.
        sql = "INSERT INTO " + str(self.test_table) + " ("
        # Get the keys set.
        key_list = list(add_fields.keys())
        # Variable for holding values.
        vals = ""
        # For each key, add the text 'key = value, ' so that each field is updated correctly.
        for i in range(len(key_list)):
            # Get the field being updated.
            field = key_list[i]
            val = add_fields[field]
            # Change how the value should look in the sql depending on it's type.
            if type(val) is str:
                value = self.connector.connect().escape(val)
            elif type(val) is int:
                value = str(val)
            elif type(val) is bool:
                value = str(val).upper()
            # Add the necessary text.
            sql += field
            vals += value
            # If this is not the last key, add a comma.
            if i < len(key_list) - 1:
                sql += ", "
                vals += ", "

        # Finish off the command.
        sql += ") VALUES (" + vals + ")"

        if self.verbose:
            print("Adding: " + sql)

        return sql

    def get_add_fields(self, rgt_status_line, event_dic, harness_tld):
        """
        Get the fields needed for adding a test.

        :param rgt_status_line: The parsed rgt status line for the test.
        :param event_dic: A parsed event.
        :param harness_tld: The path to where the events for the test are stored.
        :return: A dictionary containing the field, value combinations for adding the test.
        """
        # Initialize an empty dictionary.
        add_fields = {}

        # Add the field, value pairs to the dictionary.
        add_fields['harness_uid'] = rgt_status_line['harness_uid']
        add_fields['harness_start'] = rgt_status_line['harness_start']
        add_fields['harness_tld'] = harness_tld
        add_fields['application'] = event_dic['app']
        add_fields['testname'] = event_dic['test']
        add_fields['system'] = event_dic['rgt_system_log_tag']

        # TODO: Change this to actually put in the correct 'previous_job_id'.
        add_fields['previous_job_id'] = rgt_status_line['harness_uid']

        return add_fields

    def update_test_table(self, test_id, output_path, build_output_path, rgt_status_line):
        """
        Update the test set. This looks at the event and all current info in the rgt_status.txt file.

        :param test_id: The id of the test that needs to be updated.
        :param output_path: The path to where the outputs for the test instance exist.
        :param build_output_path: The path to where the build output is located.
        :param rgt_status_line: The line from the rgt_status.txt file that matches this test.
        :return:
        """
        # Get field, value combinations to update.
        update_fields = self.get_update_fields(rgt_status_line, output_path, build_output_path)

        # Get the necessary sql for updating the database.
        sql = self.get_update_sql(update_fields, test_id)
        db = self.connector.connect()

        execute_sql(sql, db)

        db.close()

    def get_update_sql(self, update_fields, test_id):
        """
        Get the sql for updating the database with some fields.

        :param update_fields: A dictionary containing the field to update as key and the value to change it to.
        :param test_id: The id of the test that this update is for.
        :return: The sql code to run on the database.
        """
        # Update some file.
        sql = "UPDATE " + self.test_table + " SET "
        # Get the keys set.
        key_list = list(update_fields.keys())
        # For each key, add the text 'key = value, ' so that each field is updated correctly.
        for i in range(len(key_list)):
            # Get the field being updated.
            field = key_list[i]
            val = update_fields[field]
            if type(val) is str:
                value = self.connector.connect().escape(val)
            elif type(val) is int:
                value = str(val)
            elif type(val) is bool:
                value = str(val).upper()
            # Add the necessary text.
            sql += field + " = " + value
            # If this is not the last key, add a comma.
            if i < len(key_list) - 1:
                sql += ","
            # Put a space in.
            sql += " "

        # Finish off the command so the correct test is updated. This only needs to be done for one test and there
        # should only be one test so this speeds it up so it doesn't have to check for more.
        sql += "WHERE test_id = " + str(test_id) + " LIMIT 1"

        if self.verbose:
            print("Updating: " + sql)

        return sql

    def get_update_fields(self, rgt_status_line, output_path, build_output_path):
        """
        Get the new values for each field.

        :param rgt_status_line: The line of the rgt_status file that will be used.
        :param output_path: The path to where the outputs exist.
        :param build_output_path: The path to where the build output exists.
        :return: A dictionary containing the fields and values that need to be updated.
        """
        # If the length of the line and the number of fields we know how to parse are not equal, we may try to insert
        # incorrect info.
        if len(rgt_status_line) != len(self.rgt_fields):
            warnings.warn('I do not know how to parse this line. I expected ' + str(len(self.rgt_fields))
                          + " fields but I got " + str(len(rgt_status_line)) + " fields. I will ignore this line.\n"
                          + str(rgt_status_line))
            return {}

        # LSF job id.
        job_id = rgt_status_line['job_id']
        # Check LSF.
        lsf_exit_status = self.get_exit_status(job_id)

        # Create a dictionary for holding the field, value combinations.
        update_fields = {}
        # The first and second index of the stat_line contain the start time and unique id, neither of which are needed.
        # The rest contain job_id, build_status, submit_status, and check_status.
        # Each of which are either ints or '***'. Depending on this we may or may not insert it.
        for i in range(2, len(self.rgt_fields)):
            field = self.rgt_fields[i]
            val = rgt_status_line[field]
            # Test if it is an integer. If so, put it into a field to update.
            if type(val) == int or val.isdigit():
                if field == 'check_status':
                    if self.legal_check_status(val):
                        update_fields[field] = int(val)
                    else:
                        warnings.warn('Skipping check status ' + str(val) + ' since it was not in the check table.' + self.rgt_status_path + '\n' + str(rgt_status_line))
                else:
                    update_fields[field] = int(val)

        # Test if it has an exit status. If so, record it and the job is now done.
        if lsf_exit_status is not None:
            update_fields['lsf_exit_status'] = lsf_exit_status
            update_fields['done'] = True
        # '*_status' keys that are not in the update fields are those that are not integers.
        # This is matching if there is some integer representation for that status.
        elif 'build_status' in update_fields.keys() and update_fields['build_status'] != 0:
            update_fields['done'] = True
        elif 'submit_status' in update_fields.keys() and update_fields['submit_status'] != 0:
            update_fields['done'] = True
        elif 'job_id' in update_fields.keys() and not self.in_queue(update_fields['job_id']):
            update_fields['done'] = True
        else:
            update_fields['done'] = False

        if output_path is not None:
            # For each possible output field.
            for output_field in self.possible_outputs:
                if output_field == 'build':
                    path = build_output_path
                else:
                    path = output_path
                # Try to get the text from the file.
                try:
                    output_text = self.output_text(path, output_field)
                # If the file does not exist, try to get the next file.
                except FileNotFoundError:
                    warnings.warn("Did not find file associated with '" + output_field + "' in " + path + ".")
                    # If the file has not been written yet, don't change flag to done because it may still be written.
                    if (output_field + '_status') in update_fields.keys():
                        update_fields['done'] = False
                    continue
                except PermissionError:
                    warnings.warn("Did not have permission to get output of " + path + ".", PermissionWarning)
                    # If we do not yet have permission for the file, that may change eventually.
                    if (output_field + '_status') in update_fields.keys():
                        update_fields['done'] = False
                    continue
                # If it does exist, add it as a field to update.
                else:
                    if output_text is not None:
                        key = 'output_' + output_field
                        update_fields[key] = output_text

        return update_fields

    def legal_check_status(self, check_status):
        """
        Find if the check status is in the check table.

        :param check_status: The status to match.
        :return: Whether it was in the table or not.
        """
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE check_uid = {check_status})"\
              .format(table=self.check_table, check_status=check_status)
        db = self.connector.connect()
        cursor = db.cursor()
        cursor.execute(sql)
        result = bool(cursor.fetchone()[0])
        db.commit()
        db.close()
        return result

    def output_text(self, output_path, output_type):
        """
        Get the text from the output file.

        :param output_path: Path to where all of the output files are stored.
        :param output_type: Type of output that is being checked.
        :return: The text of the output file.
        """
        # If output type is not one that is supported then inform the user.
        if output_type not in self.possible_outputs:
            warnings.warn("Output type not allowed. You entered " + output_type + ". I need something in:\n" \
                          + str(self.possible_outputs))
            return

        # Create the path to the file.
        output_file_path = os.path.join(output_path, 'output_' + output_type + '.txt')
        # Read the output file and send it back.
        with open(output_file_path) as f:
            return f.read()

    def in_queue(self, job_id):
        """
        Get whether the job exists in LSF.

        :param job_id: The id of the job.
        :return: Whether it exists.
        """
        # Test if it is not an int. If not, return.
        if type(job_id) != int:
            if not job_id.isdigit():
                return None

        # Get the job id.
        job_id = int(job_id)

        # Test if we are doing a unit test. If so, replace this function with the new one.
        if self.in_queue_function is not None:
            return self.in_queue_function(job_id)

        # Get the exit status of the job.
        JS = job_status.JobStatus()
        if len(JS.get_jobs(job_id)) == 0:
            return False
        else:
            return True

    def get_exit_status(self, job_id):
        """
        Get the lsf_exit_status of some test based on an event dictionary for that test.

        :param job_id: The id of the job to check.
        :return: The exit status of the job. If 'None' is returned, that means there was no exit status found.
        """
        # TODO: Need to somehow check the exit status if this is a job being built.
        # Test if it is not an int. If not, return.
        if type(job_id) != int:
            if not job_id.isdigit():
                return None

        # Get the job id.
        job_id = int(job_id)

        # Test if we are doing a unit test. If so, replace this function with the new one.
        if self.lsf_exit_function is not None:
            return self.lsf_exit_function(job_id)

        # Get the exit status of the job.
        JS = job_status.JobStatus()
        return JS.get_job_exit_status(job_id)

    def get_event_uid(self, event_dic):
        """
        Get the type of event that some event dictionary represents.

        :param event_dic: a dictionary for the event.
        :return: The uid for the event.
        """
        # Get the file name of the event. This is not the full path, just the name of the file.
        file_name = event_dic['event_filename']

        # Find which event code is in the file name.
        for possible_event in self.event_types:
            if str(possible_event) in file_name:
                return possible_event
        else:
            return None

    def get_event_id(self, event_uid):
        """
        Get the id of the event from the rgt_event table based on the uid for the event.

        :param event_uid: The uid of the event.
        :return: The id in the table for the event.
        """
        db = self.connector.connect()
        # Create a cursor for execution of commands.
        cursor = db.cursor()
        # Select the event_id that corresponds to the event_uid.
        sql = "SELECT event_id FROM {table} WHERE event_uid = {event_uid}"\
              .format(table=self.event_table, event_uid=event_uid)

        # Execute the command.
        cursor.execute(sql)
        db.commit()
        # Fetch the response.
        event_id = cursor.fetchone()
        db.close()
        return int(event_id[0])

    def get_test_id(self, harness_uid):
        """
        The id of the test instance in the table.

        :param harness_uid: The uid for the test.
        :return: The id for the test in the database.
        """
        # Initialize a connection.
        db = self.connector.connect()
        cursor = db.cursor()
        # Select the test id that matches with the uid.
        sql = "SELECT test_id FROM {table} WHERE harness_uid = '{harness_uid}'"\
              .format(table=self.test_table, harness_uid=harness_uid)

        # Run the command and close the connection.
        cursor.execute(sql)
        db.commit()
        harness_uid = cursor.fetchone()[0]
        db.close()
        return harness_uid
