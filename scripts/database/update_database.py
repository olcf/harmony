"""
This file updates the database using any new things in the rgt.input and all things currently in the database
that are not yet done.
"""
import os
from scripts import job_status
import warnings
from scripts import parse_file
from scripts.database import tests_to_check


class UpdateDatabase:
    """
    This class takes care of running all necessary functions for updating the database. It does not repeat.
    """
    def __init__(self, connector, rgt_input_path, test_table='rgt_test', test_event_table='rgt_test_event',
                 event_table='rgt_event', verbose=True):
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
        self.db = connector.connect()

        # Set the path to where new tests come from.
        self.rgt_input_path = rgt_input_path

        # TODO: Is specification of event_types needed?
        # Set the types of events we are prepared to handle.
        self.event_types = [110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
        # The fields within an rgt_status.txt file.
        self.rgt_fields = ['harness_start', 'harness_uid', 'job_id', 'build_status', 'submit_status', 'check_status']

        # The possible output files that we are prepared to handle. They will go like "*_output.txt".
        self.possible_outputs = ['build', 'submit', 'check', 'report']

        # The names of the different tables to use. This is useful when doing unit tests so that the actual tables
        # are not getting messed up with our tomfoolery.
        self.test_table = test_table
        self.test_event_table = test_event_table
        self.event_table = event_table

        # TODO: add verbose statements.
        self.verbose = verbose

    def update(self):
        """
        Update the database based on current info and rgt path.

        :return:
        """
        # Create finder to find the necessary tests.
        finder = tests_to_check.testFinder(self.connector, self.rgt_input_path, rgt_test_table=self.test_table)
        if self.verbose:
            print("Adding new tests from " + self.rgt_input_path + ".")
        # Add all new tests in the rgt_path.
        finder.add_new_tests()

        # Get all the tuples of tests that are not yet done.
        test_tups = self.get_not_done_tests()

        # Go through each of these tests and update the necessary material.
        for i in range(len(test_tups)):
            # Set the current test tuple.
            test_tup = test_tups[i]
            # Third entry contains the path to the test instance. The directory above that one contains the
            # 'rgt_status.txt' file.
            rgt_stat_path = os.path.join(os.path.dirname(test_tup[2]), 'rgt_status.txt')
            # Get the line in the rgt_status file that matches this uid.
            stat_line = self.get_rgt_stat_line(rgt_stat_path, test_tup[1])

            if self.verbose:
                print("Getting events for " + str(test_tup) + ".")
            # Get a list of all events for this test instance. We sort them so that we can check the last test for the
            # lsf exit status.
            event_paths = sorted(self.get_event_paths(test_tups[2]))
            if self.verbose:
                if len(event_paths) == 1:
                    print("Found 1 event. The path is " + str(event_paths) + ".")
                else:
                    print("Found " + str(len(event_paths)) + " events. The paths are " + str(event_paths) + ".")

            # If there are events, start updating.
            if len(event_paths) != 0:
                # Get the test_id for this instance.
                test_id = test_tup[0]
                # For each event, insert it into the event table connected to the correct event.
                for j in range(len(event_paths)):
                    event_path = event_paths[j]
                    self.insert_into_event_table(test_tup[0], event_path)

                # Get the last event's path.
                last_event_path = event_paths[-1]
                # Insert new information into the main table.
                self.update_test_table(test_id, last_event_path, stat_line)

    def in_event_table(self, test_id, event_id):
        """
        Test if some event already exists in the table.

        :param test_id: The id that this event is connected to.
        :param event_id: The id of the event to check. Each event_id only happens once.
        :return: Whether the event already existed.
        """
        # Create a cursor for executing on the database.
        cursor = self.db.cursor()
        # Test if the test, event combo exists in the table.
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE test_id = {test_id} AND event_id = {event_id})"\
              .format(table=self.test_event_table, test_id=test_id, event_id=event_id)

        # Execute the command.
        cursor.execute(sql)
        # Return whether or not it was in the table.
        in_table = cursor.fetchone()
        return bool(in_table)

    def get_rgt_stat_line(self, rgt_stat_path, harness_uid):
        """
        Get the relevant line of the rgt_status.txt file for some harness_uid.

        :param rgt_stat_path: Path to the rgt_status.txt file.
        :param harness_uid: The uid of the test that will be matched.
        :return: The split line of the rgt_status.txt file.
        """
        # Create a parser for the status file.
        parser = parse_file.ParseRGTStatus()
        # Get the job dictionaries from each line.
        job_dics = parser.parse_file(rgt_stat_path)
        # Go through backwards because the newest harness uid will be at the end and since this uid is not yet done,
        # it will most likely be at the end.
        for i in range(start=len(job_dics) - 1, stop=-1, step=-1):
            # If the harness_uid match, then return the line.
            if job_dics[i]['harness_uid'] == harness_uid:
                return job_dics[i]
        # If nothing matched, there is a big problem.
        raise KeyError("Could not find " + str(harness_uid) + " in " + rgt_stat_path + ".")

    def get_not_done_tests(self):
        """
        Get all paths to tests that are not yet done.

        :return: List of tuples containing test_id and path.
        """
        # Create a cursor to act on the database.
        cursor = self.db.cursor()
        # Select only the path to the test for each test that is not done. Group by path so that we only need to read
        # the rgt_status.txt file once.
        sql = "SELECT (test_id, harness_uid, harness_tld) FROM {table} WHERE done = FALSE GROUP BY harness_tld"\
              .format(table=self.rgt_test_table)
        # Execute the command.
        cursor.execute(sql)
        # Get the response.
        test_tups = list(cursor.fetchall())
        return test_tups

    def get_event_paths(self, test_instance_path):
        """
        Get the paths to all events for some test instance.

        :param test_instance_path: The path to where the test instance is stored.
        :return: A list containing the paths to all events for that test.
        """
        # Setup a list for holding the events.
        events = []
        # Get all immediate subfiles.
        for file in os.listdir(test_instance_path):
            # Filter to only get Events.
            if 'Event_' in file:
                # Check that the event is one that we are prepared to handle.
                for possible_event in self.event_types:
                    if str(possible_event) in file:
                        events.append(os.path.join(test_instance_path, file))
                        break
                # If it is not, give a warning that we are skipping it.
                else:
                    warnings.warn("I don't understand this event file. It is a code that I am not prepared to handle.\n"
                                  + os.path.join(test_instance_path, file))
        # Return file paths.
        return events

    def insert_into_event_table(self, test_id, event_path):
        """
        Insert some event into the event table.

        :param test_id: The id of the test that this event is for.
        :param event_path: The path to the event file.
        :return:
        """
        # TODO: Add output if it exists.
        # Parse the important info from the event file.
        parser = parse_file.ParseEvent()
        # Get the dictionary for the event.
        event_dic = parser.parse_file(event_path)
        # Get the events uid.
        event_uid = self.get_event_uid(event_dic)
        # Get the id of the event from the 'rgt_event' table.
        event_id = self.get_event_id(event_uid)

        # If it does not already exist in the table, put it in.
        if not self.in_event_table(test_id, event_id):
            # Get time when event occured.
            event_time = event_dic['event_time'].replace('T', ' ')

            # Enter it into the 'rgt_test_event' table.
            self.insert_parsed_event_into_event_table(test_id, event_id, event_time)

    def update_test_table(self, test_id, event_path, rgt_stat_line):
        """
        Update the test set. This looks at the event and all current info in the rgt_status.txt file.

        :param test_id: The id of the test that needs to be updated.
        :param event_path: The path to the most recent event for that test.
        :param rgt_stat_line: The line from the rgt_status.txt file that matches this test.
        :return:
        """
        # Create parser for parsing event.
        parser = parse_file.ParseEvent()
        # Get event dictionary.
        event_dic = parser.parse_file(event_path)

        # LSF job id.
        job_id = rgt_stat_line['job_id']
        # Check LSF.
        lsf_exit_status = self.get_exit_status(job_id)

        # Update 'rgt_test' with new status.
        update_fields = self.get_update_fields(rgt_stat_line)

        # Test if it has an exit status. If so, record it and the job is now done.
        if lsf_exit_status is not None:
            update_fields['lsf_exit_status'] = lsf_exit_status
            update_fields['done'] = True
        # If the test does not have an exit status but one of it's other stats are non zero and not 17 (running)
        # then change the done status.
        else:
            for status in ['build_status', 'submit_status', 'check_status']:
                if status in update_fields.keys():
                    if update_fields[status] not in [0, 17]:
                        update_fields['done'] = True
                        break

        # Get the necessary sql for updating the database.
        sql = self.get_update_sql(update_fields, test_id)
        # Create a cursor for execution of sql on the database.
        cursor = self.db.cursor()

        # Execute the command.
        cursor.execute(sql)
        # Commit it to the database.
        self.db.commit()

    def get_update_sql(self, update_fields, test_id):
        """
        Get the sql for updating the database with some fields.

        :param update_fields: A dictionary containing the field to update as key and the value to change it to as the,
        well, value.
        :param test_id: The id of the test that this update is for.
        :return:
        """
        # Update some file.
        sql = "UPDATE " + self.test_table + " SET "
        # Get the keys set.
        key_list = list(update_fields.keys())
        # For each key, add the text 'key = value, ' so that each field is updated correctly.
        for i in range(len(key_list)):
            # Get the field being updated.
            field = key_list[i]
            # Add the necessary text.
            sql += field + " = " + update_fields[field]
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

    def get_update_fields(self, rgt_stat_line):
        """
        Get the new values for each field.

        :param rgt_stat_line: The line of the rgt_status file that will be used.
        :return:
        """
        # If the length of the line and the number of fields we know how to parse are not equal, we may try to insert
        # incorrect info.
        if len(rgt_stat_line) != len(self.rgt_fields):
            raise IndexError('I do not know how to parse this line. I expected ' + str(len(self.rgt_fields))
                             + " fields but I got " + str(len(rgt_stat_line)) + " fields.\n" + str(rgt_stat_line))

        # Create a dictionary for holding the field, value combinations.
        update_fields = {}
        # The first and second index of the stat_line contain the start time and unique id, neither of which are needed.
        # The rest contain job_id, build_status, submit_status, and check_status.
        # Each of which are either ints or '***'. Depending on this we may or may not insert it.
        for i in range(start=2, stop=len(rgt_stat_line)):
            # Test if it is an integer. If so, put it into a field to update.
            if rgt_stat_line[i].isdigit():
                update_fields[self.rgt_fields[i]] = int(rgt_stat_line)

        return update_fields

    def output_text(self, output_path, output_type):
        """
        Get the text from the output file.

        :param output_path: Path to where all of the output files are stored.
        :param output_type: Type of output that is being checked.
        :return: The text of the output file.
        """
        # If output type is not one that is supported then inform the user.
        if output_type not in self.possible_outputs:
            error_string = "Output type not allowed. You entered " + output_type + ". I need something in:\n" \
                           + str(self.possible_outputs)
            raise KeyError(error_string)

        # Create the path to the file.
        output_file_path = os.path.join(output_path, 'output_' + output_type + '.txt')
        # Read the ouput file and send it back.
        with open(output_file_path) as f:
            return f.read()

    def get_exit_status(self, job_id):
        """
        Get the lsf_exit_status of some test based on an event dictionary for that test.

        :param job_id: The id of the job to check.
        :return: The exit status of the job. If 'None' is returned, that means there was no exit status found.
        """
        # TODO: Need to somehow check the exit status if this is a job being built.
        # Test if it is not an int. If not, return.
        if not job_id.isdigit():
            return None

        # Get the job id.
        job_id = int(job_id)
        # Get the exit status of the job.
        JS = job_status.JobStatus()
        return JS.get_job_exit_status(job_id)

    def insert_parsed_event_into_event_table(self, test_id, event_id, event_time):
        """
        Insert an event file after splitting into the relevant information.

        :param test_id: The id of the test that this event is for.
        :param event_id: The id of the event.
        :param event_time: When the event occurred.
        :return:
        """
        # Create cursor for execution of commands.
        cursor = self.db.cursor()
        # Insert the necessary info into the table.
        sql = "INSERT INTO {table} (test_id, event_id, event_time) " \
              "VALUES ({test_id}, {event_id}, {event_time})"\
              .format(table=self.test_event_table, test_id=test_id, event_id=event_id, event_time=event_time)

        # Execute the command.
        cursor.execute(sql)
        # Commit it to the database.
        self.db.commit()

    def get_event_uid(self, event_dic):
        """
        Get the type of event that some event dictionary represents.

        :param event_dic: a dictionary for the event.
        :return:
        """
        # Get the file name of the event. This is not the full path, just the name of the file.
        file_name = event_dic['event_filename']

        # Find which event code is in the file name.
        for possible_event in self.event_types:
            if str(possible_event) in file_name:
                return possible_event

    def get_event_id(self, event_uid):
        """
        Get the id of the event from the rgt_event table based on the uid for the event.

        :param event_uid: The uid of the event.
        :return: The id in the table for the event.
        """
        # Create a cursor for execution of commands.
        cursor = self.db.cursor()
        # Select the event_id that corresponds to the event_uid.
        sql = "SELECT event_id FROM {table} WHERE event_uid = {event_uid}"\
              .format(table=self.event_table, event_uid=event_uid)

        # Execute the command.
        cursor.execute(sql)
        # Fetch the response.
        event_id = cursor.fetchone()
        return int(event_id[0])
