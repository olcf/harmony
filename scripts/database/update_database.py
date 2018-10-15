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
    def __init__(self, connector, test_table='rgt_test', test_event_table='rgt_test_event', event_table='rgt_event',
                 verbose=True):
        self.event_types = [110, 120, 130, 140, 150, 160, 170, 180, 190, 200]
        self.db = connector.connect()
        self.rgt_fields = ['harness_start', 'harness_uid', 'job_id', 'build_status', 'submit_status', 'check_status']

        self.test_table = test_table
        self.test_event_table = test_event_table
        self.event_table = event_table

        # TODO: add verbose statements.
        self.verbose = verbose

    def update(self):
        finder = tests_to_check.testFinder()
        finder.add_new_tests()

        test_tups = self.get_not_done_tests()

        for i in range(len(test_tups)):
            test_tup = test_tups[i]
            # 3 entry contains the path to the test instance. The directory above that one containts the
            # 'rgt_status.txt' file.
            rgt_stat_path = os.path.join(os.path.dirname(test_tup[2]), 'rgt_status.txt')
            # Get the line in the rgt_status file that matches this uid.
            stat_line = self.get_rgt_stat_line(rgt_stat_path, test_tup[1])

            event_paths = sorted(self.get_event_paths(test_tups[2]))
            if len(event_paths) != 0:
                test_id = test_tup[0]
                for j in range(len(event_paths)):
                    event_path = event_paths[j]
                    self.insert_into_event_table(test_tup[0], event_path)

                last_event_path = event_paths[-1]
                self.insert_into_test_table(test_id, last_event_path, stat_line)

    def in_event_table(self, test_id, event_id):
        cursor = self.db.cursor()
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE test_id = {test_id} AND event_id = {event_id})"\
              .format(table=self.test_event_table, test_id=test_id, event_id=event_id)

        cursor.execute(sql)
        in_table = cursor.fetchone()
        return bool(in_table)

    def get_rgt_stat_line(self, path, harness_uid):
        parser = parse_file.ParseRGTStatus()
        job_dics = parser.parse_file(path)
        # Go through backwards because the newest harness uid will be at the end and since this uid is not yet done,
        # it will most likely be at the end.
        for i in range(start=len(job_dics) - 1, stop=-1, step=-1):
            if job_dics[i]['harness_uid'] == harness_uid:
                return job_dics[i]
        raise KeyError("Could not find " + str(harness_uid) + " in " + path + ".")

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

    def get_stat_lines(self, rgt_status_path, harness_uids):
        # Copy the harness_uids so that we can mess with the list without changing the actual list.
        uids = harness_uids[:]
        parser = parse_file.ParseRGTStatus()
        job_dics = parser.parse_file(rgt_status_path)

        stat_lines = {}
        for i in range(start=len(job_dics)-1, stop=-1, step=-1):
            for uid in uids:
                if uid == job_dics[i]['harness_uid']:
                    stat_lines[uid] = job_dics[i]
                    uids.remove(uid)
            if len(uids) == 0:
                break

        return stat_lines

    def insert_into_event_table(self, test_id, event_path):
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

    def insert_into_test_table(self, test_id, event_path, rgt_stat_line):
        # Create parser for parsing event.
        parser = parse_file.ParseEvent()
        # Get event dictionary.
        event_dic = parser.parse_file(event_path)

        # Check LSF.
        lsf_exit_status = self.get_exit_status(event_dic)

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

        sql = self.get_update_sql(update_fields, test_id)
        cursor = self.db.cursor()

        cursor.execute(sql)
        self.db.commit()

    def get_update_sql(self, update_fields, test_id):
        sql = "UPDATE " + self.test_table + " SET "
        key_list = list(update_fields.keys())
        for i in range(len(key_list)):
            field = key_list[i]
            sql += field + " = " + update_fields[field]
            if i < len(key_list) - 1:
                sql += ","
            sql += " "

        sql += "WHERE test_id = " + str(test_id) + " LIMIT 1"

        if self.verbose:
            print("Updating: " + sql)

        return sql

    def get_update_fields(self, rgt_stat_line):
        # The first and second index contain the start time and unique id, neither of which are needed.
        # The rest contain job_id, build_status, submit_status, and check_status.
        # Each of which are either ints or '***'. Depending on this we may or may not insert it.
        if len(rgt_stat_line) != len(self.rgt_fields):
            raise IndexError('I do not know how to parse this line. I expected ' + str(len(self.rgt_fields))
                             + " fields but I got " + str(len(rgt_stat_line)) + " fields.\n" + str(rgt_stat_line))

        update_fields = {}
        for i in range(start=2, stop=len(rgt_stat_line)):
            # Test if it is an integer. If so, put it into a field to update.
            if rgt_stat_line[i].isdigit():
                update_fields[self.rgt_fields[i]] = int(rgt_stat_line)

        return update_fields

    def output_text(self, output_path, output_type):
        possible_outputs = ['build', 'submit', 'check', 'report']
        if output_type not in possible_outputs:
            error_string = "Output type not allowed. You entered " + output_type + ". I need something in:\n" \
                           + str(possible_outputs)
            raise KeyError(error_string)

        output_file_path = os.path.join(output_path, 'output_' + output_type + '.txt')
        try:
            with open(output_file_path) as f:
                return f.read()
        except FileNotFoundError:
            return None

    def get_exit_status(self, event_dic):
        # TODO: Need to somehow check the exit status if this is a job being built.
        # Test if it is not an int. If not, return.
        if not event_dic['job_id'].isdigit():
            return None

        # Get the job id.
        job_id = int(event_dic['job_id'])
        # Get the exit status of the job.
        JS = job_status.JobStatus()
        return JS.get_job_exit_status(job_id)

    def insert_parsed_event_into_event_table(self, test_id, event_id, event_time):
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
        # Get the file name of the event.
        file_name = event_dic['event_filename']
        # Find which event code is in the file name.
        for possible_event in self.event_types:
            if str(possible_event) in file_name:
                return possible_event

    def get_event_id(self, event_uid):
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
