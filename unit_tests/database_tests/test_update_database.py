import unittest
import os
from scripts.database import update_database
from scripts.database import create_database
from scripts import config_functions
from scripts.database import connect_database
import shutil
from random import random


class InstanceCreator:
    class InstancePaths:
        def __init__(self):
            return

    def __init__(self):
        self.path_to_inputs = os.path.abspath(os.path.join(__file__, '..', '..', 'test_inputs', 'database_inputs'))
        self.path_to_rgt_input = os.path.join(self.path_to_inputs, 'rgt_input.txt')
        self.path_to_exit_files = os.path.join(self.path_to_inputs, 'lsf_exit_files')
        self.path_to_output_files = os.path.join(self.path_to_inputs, 'output_files')
        self.path_to_example_tests = os.path.join(self.path_to_inputs, 'example_tests_for_database')

    def create_test_instance(self, program_name, test_name, instance_name, time, job_id, build_status, submit_status,
                             check_status, outputs, system, events, exit_status):
        instance = self.InstancePaths()
        instance.run_archive_instance_path, instance.status_instance_path = \
            self.make_directories(program_name, test_name, instance_name, self.path_to_example_tests)

        instance.path_to_rgt_status = os.path.join(os.path.dirname(instance.status_instance_path), 'rgt_status.txt')
        self.write_rgt_status(instance.path_to_rgt_status, time, instance_name, job_id, build_status, submit_status, check_status)

        self.write_rgt_input(self.path_to_rgt_input, self.path_to_example_tests, program_name, test_name)

        for output_key in outputs.keys():
            instance.output_path = os.path.join(instance.run_archive_instance_path, 'output_' + output_key + ".txt")
            self.write_output(instance.output_path, outputs[output_key])

        complete_events = {}
        event_paths = {}
        for event_key in events.keys():
            event_dic = events[event_key]
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
            event_path = os.path.join(instance.status_instance_path, file_name)
            self.write_event(event_path, event_dic)

            complete_events[event_key] = event_dic
            event_paths[event_key] = event_path
        instance.complete_events = complete_events
        instance.event_paths = event_paths

        self.write_exit_value(job_id, exit_status)

        return instance

    @staticmethod
    def create_rgt_status_line(harness_start, harness_uid, job_id, build_status, submit_status, check_status):
        return {'harness_start': harness_start, 'harness_uid': harness_uid, 'job_id': job_id,
                'build_status': build_status, 'submit_status': submit_status, 'check_status': check_status}

    @staticmethod
    def write_event(path_to_event, event_dic):
        # Events need 'event_time' and 'run_archive' keys to function correctly.
        text = ""
        for key in event_dic.keys():
            text += "{key}={value} ".format(key=key, value=event_dic[key])

        with open(path_to_event, mode='w+') as f:
            f.write(text)

    def write_output(self, output_filename, text):
        with open(os.path.join(self.path_to_output_files, output_filename), "w+") as f:
            f.write(text)

    @staticmethod
    def write_rgt_status(path_to_rgt_status, harness_start, harness_uid, job_id, build_status, submit_status, check_status):
        text = ""
        mode = "a"
        if not os.path.exists(path_to_rgt_status):
            text += "##################################\n" + \
                    "# Start time   Unique ID   Batch ID    Build Status    Submit Status   Check Status\n" + \
                    "##################################\n"
            mode = "w+"

        text += "{harness_start} {harness_uid} {job_id} {build_status} {submit_status} {check_status}\n" \
            .format(harness_start=harness_start, harness_uid=harness_uid, job_id=job_id,
                    build_status=build_status, submit_status=submit_status, check_status=check_status)

        with open(path_to_rgt_status, mode=mode) as f:
            f.write(text)

    @staticmethod
    def make_directory(directory_path):
        if not os.path.exists(directory_path):
            os.mkdir(directory_path)

    def make_directories(self, program_name, test_name, instance_name, path_to_example_tests):
        program_path = os.path.join(path_to_example_tests, program_name)
        self.make_directory(program_path)

        test_path = os.path.join(program_path, test_name)
        self.make_directory(test_path)

        status_path = os.path.join(test_path, 'Status')
        self.make_directory(status_path)
        run_archive_path = os.path.join(test_path, 'Run_Archive')
        self.make_directory(run_archive_path)

        status_instance_path = os.path.join(status_path, instance_name)
        self.make_directory(status_instance_path)
        run_archive_instance_path = os.path.join(run_archive_path, instance_name)
        self.make_directory(run_archive_instance_path)

        return run_archive_instance_path, status_instance_path

    def replacement_lsf_exit_function(self, job_id):
        file_path = os.path.join(self.path_to_exit_files, str(job_id) + '_exit_status.txt')
        with open(file_path, mode='r') as f:
            exit_value = f.read()

        if len(exit_value) == 0:
            return None
        else:
            return int(exit_value)

    def write_exit_value(self, job_id, value):
        file_path = os.path.join(self.path_to_exit_files, str(job_id) + '_exit_status.txt')
        with open(file_path, mode='w+') as f:
            if value is None:
                f.write('')
            else:
                f.write(value)

    @staticmethod
    def write_rgt_input(path_to_rgt_input, path_to_tests, program_name, test_name):
        mode = 'a'
        text = ""
        if not os.path.exists(path_to_rgt_input):
            mode = 'w+'
            text += "path_to_tests = " + path_to_tests + "\n"

        text += "test = " + program_name + " " + test_name + "\n"

        with open(path_to_rgt_input, mode=mode) as f:
            f.write(text)

class TestUpdateDatabase(unittest.TestCase):
    """
    This class tests that updating the database works correctly.
    """
    def init_directories(self):
        self.IC.make_directory(self.IC.path_to_exit_files)
        self.IC.make_directory(self.IC.path_to_output_files)
        self.IC.make_directory(self.IC.path_to_example_tests)

    def remove_directories(self):
        for file in os.listdir(self.IC.path_to_inputs):
            file_path = os.path.join(self.IC.path_to_inputs, file)

            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

    def setUp(self):
        """
        Each time a new test is run. Create new tables to act on.

        :return:
        """
        self.test_table = 'test_rgt_test'
        self.test_event_table = 'test_rgt_event'
        self.event_table = 'test_rgt_event'
        self.IC = InstanceCreator()

        database_conf = config_functions.get_config()['DATABASE']
        self.connector = connect_database.DatabaseConnector(database_conf)

        create_tables_path = os.path.join(os.path.dirname(__file__), 'create_test_tables.sql')
        create_database.execute_sql_file(self.connector, create_tables_path)

        self.init_directories()

    def tearDown(self):
        """
        Drop all tables made for testing after each test case.

        :return:
        """
        drop_tables_path = os.path.join(os.path.dirname(__file__), 'drop_test_tables.sql')
        create_database.execute_sql_file(self.connector, drop_tables_path)
        self.remove_directories()

    def init_update_database(self, rgt_input_path=''):
        self.UD = update_database.UpdateDatabase(self.connector, rgt_input_path, test_table=self.test_table,
                                                 test_event_table=self.test_event_table, event_table=self.event_table,
                                                 replacement_lsf_exit_function=self.IC.replacement_lsf_exit_function)

    def insert_event(self, event_uid, event_name='test'):
        print("Connecting.")
        db = self.connector.connect()
        cursor = db.cursor()

        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uid, event_name=event_name)
        print("Inserting event.")
        cursor.execute(sql)
        print("Commiting.")
        db.commit()
        db.close()

    def in_table(self, table_name, **kwargs):
        sql = "SELECT EXISTS(SELECT 1 FROM {table} WHERE".format(table=table_name)
        key_list = kwargs.keys()
        for i in range(len(kwargs)):
            key = key_list[i]
            val = kwargs[key]

            if type(val) is int:
                val_string = str(val)
            elif type(val) is str:
                val_string = "'" + val + "'"

            sql += " " + key + " = " + val_string
            if i < len(kwargs) - 1:
                sql += " AND"

        sql += ")"

        db = self.connector.connect()
        cursor = db.cursor()
        cursor.execute(sql)
        return bool(cursor.fetchone()[0])

    def test_get_event_id(self):
        event_uid = 0
        print("Inserting event.")
        self.insert_event(event_uid, 'test')

        self.init_update_database()
        print("Getting event id.")
        event_id = self.UD.get_event_id(event_uid)
        self.assertEqual(0, event_id)

        event_uid = 1
        self.insert_event(event_uid, 'test')
        event_id = self.UD.get_event_id(event_uid)
        self.assertEqual(1, event_id)

    def test_get_event_uid(self):
        self.insert_event(0)
        self.insert_event(1)
        self.insert_event(2)

        self.init_update_database()

        event_dic = {'event_filename': 'Event_0.txt'}
        event_uid = self.UD.get_event_uid(event_dic)
        self.assertEqual(event_uid, 0)

        event_dic = {'event_filename': 'Event_3.txt'}
        event_uid = self.UD.get_event_uid(event_dic)
        self.assertIsNone(event_uid)

    def test_insert_parsed_event_into_event_table(self):
        # Insert a new test into the test table. This is because of the unique key is needed.
        db = self.connector.connect()
        with db.cursor() as cursor:
            sql = "INSERT INTO test_rgt_test (harness_uid, harness_start, harness_tld, application, testname, system, next_harness_uid, done)" \
                  " VALUES (2, 0000-00-00, 'path', 'app', 'test', 'sys', 1, FALSE)"
            cursor.execute(sql)
        db.commit()

        # Insert a new event into the event table. This is once agian because the unique key is needed.
        self.insert_event(1)

        self.init_update_database()

        self.UD.insert_parsed_event_into_event_table(0, 0, '0000-00-01')

        with db.cursor() as cursor:
            self.assertTrue(self.in_table(self.test_event_table, **{'test_id': 0}))
            self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 0}))

    def test_get_exit_status(self):
        job_id_0 = 0
        exit_status_0 = 0
        self.IC.write_exit_value(job_id_0, exit_status_0)

        job_id_1 = 1
        exit_status_1 = 1
        self.IC.write_exit_value(job_id_1, exit_status_1)

        self.init_update_database()

        self.assertEqual(exit_status_0, self.UD.get_exit_status(job_id_0))
        self.assertEqual(exit_status_1, self.UD.get_exit_status(job_id_1))

    def test_output_text(self):
        self.init_update_database()

        self.assertIsNone(self.UD.output_text('path', 'bad_output'))

        output_type = 'build'
        output_filename = 'output_' + output_type + '.txt'
        text = 'Example output text.'
        self.IC.write_output(output_filename, text)

        self.assertEqual(text, self.UD.output_text(self.IC.path_to_output_files, output_type))

    def test_get_update_fields_bad_rgt(self):
        bad_rgt_line = {'incorrect': 'length'}
        self.init_update_database()

        self.UD.get_update_fields(bad_rgt_line, {})

    def test_get_update_fields_good_building(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0000'
        harness_uid = 'instance'
        job_id = 10
        build_status = '17'
        submit_status = '***'
        check_status = '***'
        build_output_text = 'building . . .'
        submit_output_text = ''
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = None

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        self.init_update_database()

        update_fields = self.UD.get_update_fields(rgt_line, instance.complete_events['0']['run_archive'])

        # There should be keys for all things that can change while a test is running.
        # No exit status key because it is set to null and no status problems.
        # No submit or check status because they are both not integers.
        # Expect output build and submit because they will both have files.
        expected_result = {'job_id': job_id, 'build_status': int(build_status),
                           'output_build': build_output_text, 'output_submit': submit_output_text}
        for key in expected_result.keys():
            self.assertIn(key, update_fields.keys())

            self.assertEqual(expected_result[key], update_fields[key])

        # Check that there are no keys that should not be in there.
        for key in update_fields.keys():
            self.assertIn(key in expected_result.keys())

    def test_get_update_fields_good_exited(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0000'
        harness_uid = 'instance'
        job_id = 2
        build_status = '0'
        submit_status = '17'
        check_status = '***'
        build_output_text = 'building . . . \nAll done'
        submit_output_text = 'submitting . . .\n Submitted'
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = 140

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        self.init_update_database()

        update_fields = self.UD.get_update_fields(rgt_line, instance.complete_events['0']['run_archive'])

        # There should be keys for all things that can change while a test is running.
        # Expect exit status since it is set.
        # No check status because it is not an int.
        # Expect output build and submit because they will both have files.
        expected_result = {'job_id': job_id, 'build_status': int(build_status), 'submit_status': int(submit_status),
                           'output_build': build_output_text, 'output_submit': submit_output_text,
                           'lst_exit_status': exit_status, 'done': True}
        for key in expected_result.keys():
            self.assertIn(key, update_fields.keys())

            self.assertEqual(expected_result[key], update_fields[key])

        # Check that there are no keys that should not be in there.
        for key in update_fields.keys():
            self.assertIn(key in expected_result.keys())

    def test_get_update_sql(self):
        update_fields = {'int_1': 10, 'int_2': 20, 'str_1': 'one', 'str_2': 'two'}
        test_id = 100

        self.init_update_database()

        sql = self.UD.get_update_sql(update_fields, test_id)

        self.assertIn('UPDATE test_rgt_test', sql)
        self.assertIn('int_1 = 10', sql)
        self.assertIn('int_2 = 20', sql)
        self.assertIn("str_1 = 'one'", sql)
        self.assertIn("str_2 = 'two'", sql)
        self.assertIn('WHERE', sql)
        self.assertIn('test_id = ' + str(test_id), sql)

    def test_update_test_table(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ({harness_uid}, {harness_start}, {harness_tld}, " \
              "{application}, {testname}, {system}, {next_harness_uid}, {done})"\
              .format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                      application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)
        cursor.execute(sql)
        db.commit()
        self.init_update_database()
        self.UD.update_test_table(0, instance.event_paths['0']['run_archive'], rgt_line)

        expected_vals = {'harness_uid': harness_uid, 'output_build': outputs['build'],
                         'output_submit': outputs['submit'], 'output_check': outputs['check'],
                         'job_id': job_id, 'build_status': build_status, 'submit_status': submit_status,
                         'system': system}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

    def test_get_add_fields(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0000'
        harness_uid = 'instance'
        job_id = 2
        build_status = '0'
        submit_status = '17'
        check_status = '***'
        build_output_text = 'building . . . \nAll done'
        submit_output_text = 'submitting . . .\n Submitted'
        outputs = {'build': build_output_text, 'submit': submit_output_text}
        system = 'system'
        events = {'0': {}}
        exit_status = 140

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        self.init_update_database()

        job_path = instance.status_instance_path
        add_fields = self.UD.get_add_fields(rgt_line, instance.complete_events['0'])

        # There should be keys for all things that can change while a test is running.
        # Expect exit status since it is set.
        # No check status because it is not an int.
        # Expect output build and submit because they will both have files.
        expected_result = {'harness_uid': harness_uid, 'harness_start': time, 'harness_tld': job_path,
                           'application': program_name, 'testname': test_name, 'system': system,
                           'next_harness_uid': harness_uid}
        for key in expected_result.keys():
            self.assertIn(key, add_fields.keys())

            self.assertEqual(expected_result[key], add_fields[key])

        # Check that there are no keys that should not be in there.
        for key in add_fields.keys():
            self.assertIn(key in expected_result.keys())

    def test_get_add_sql(self):
        update_fields = {'int_1': 10, 'int_2': 20, 'str_1': 'one', 'str_2': 'two'}

        self.init_update_database()

        sql = self.UD.get_add_fields(update_fields)

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
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        harness_tld = instance.status_instance_path

        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0']['run_archive'], rgt_line, harness_tld)

        expected_vals = {'harness_uid': harness_uid, 'output_build': outputs['build'],
                         'output_submit': outputs['submit'], 'output_check': outputs['check'],
                         'job_id': job_id, 'build_status': build_status, 'submit_status': submit_status,
                         'system': system}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

    def test_in_event_table(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        harness_tld = instance.status_instance_path

        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0']['run_archive'], rgt_line, harness_tld)

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})"\
              .format(table=self.event_table, event_uid=event_uid, event_name='event')
        cursor.execute(sql)
        db.commit()

        sql = "INSERT INTO {table} (test_id, event_id, event_time) " \
              "VALUES ({test_id}, {event_id}, {event_time})"\
              .format(table=self.test_event_table, test_id=0, event_id=event_uid, event_time=time)
        cursor.execute(sql)
        db.commit()

        self.assertTrue(self.UD.in_event_table(0, int(event_uid)))

    def test_insert_into_event_table(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        harness_tld = instance.status_instance_path

        self.init_update_database()
        self.UD.add_to_test_table(instance.event_paths['0']['run_archive'], rgt_line, harness_tld)

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uid, event_name='event')
        cursor.execute(sql)
        db.commit()

        self.assertFalse(self.UD.in_event_table(0, int(event_uid)))
        self.UD.insert_into_event_table(0, instance.event_paths['0'])
        self.assertTrue(self.UD.in_event_table(0, int(event_uid)))

    def test_update_test_event_table(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        status_path = instance.status_instance_path

        self.init_update_database()
        event_paths = self.UD.get_event_paths(status_path)

        expected_paths = [instance.event_paths[key] for key in instance.event_paths.keys()]

        for expected_path in expected_paths:
            self.assertIn(expected_path, event_paths)

        for event_path in event_paths:
            self.assertIn(event_path, expected_paths)

    def test_add_test_instance(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uids[0], event_name='event')
        cursor.execute(sql)
        db.commit()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uids[1], event_name='event')
        cursor.execute(sql)
        db.commit()

        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        expected_vals = {'harness_uid': harness_uid, 'job_id': job_id, 'build_status': build_status,
                         'submit_status': submit_status}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

        expected_event_vals = {'0': {'event_id': 0}, '1': {'event_id': 1}}

        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['0']))
        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['1']))

    # TODO: Make method for adding in event uids. Also simplify test instance introduction.
    def test_update_test_instance(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uids[0], event_name='event')
        cursor.execute(sql)
        db.commit()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=event_uids[1], event_name='event')
        cursor.execute(sql)
        db.commit()

        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ({harness_uid}, {harness_start}, {harness_tld}, " \
              "{application}, {testname}, {system}, {next_harness_uid}, {done})" \
                  .format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                          application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)
        cursor.execute(sql)
        db.commit()

        rgt_line = self.IC.create_rgt_status_line(time, harness_uid, job_id, build_status, submit_status, check_status)
        instance = self.IC.create_test_instance(program_name, test_name, harness_uid, time, job_id, build_status,
                                                submit_status, check_status, outputs, system, events, exit_status)

        expected_vals = {'harness_uid': harness_uid, 'job_id': job_id, 'build_status': build_status,
                         'submit_status': submit_status, 'output_build': build_output_text}
        self.assertTrue(self.in_table(self.test_table, **expected_vals))

        expected_event_vals = {'0': {'event_id': 0}, '1': {'event_id': 1}}

        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['0']))
        self.assertTrue(self.in_table(self.event_table, **expected_event_vals['1']))

    def test_get_job_tuple(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ({harness_uid}, {harness_start}, {harness_tld}, " \
              "{application}, {testname}, {system}, {next_harness_uid}, {done})" \
                  .format(table=self.test_table, harness_uid=harness_uid, harness_start=time, harness_tld='path',
                          application=program_name, testname=test_name, system=system, next_harness_uid=harness_uid, done=False)
        cursor.execute(sql)
        db.commit()

        self.init_update_database()
        job_tuple = self.UD.get_job_tuple(harness_uid)
        self.assertEqual(job_tuple[0], 0)
        self.assertEqual(job_tuple[1], False)

    def test_update_test_instances(self):
        program_name = 'program'
        test_name = 'test'
        time = '00:00:0300'
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

        instance_A = self.IC.create_test_instance(program_name, test_name, harness_uids[0], time, job_id, build_status,
                                                  submit_status, check_status, outputs, system, events, exit_status)
        instance_B = self.IC.create_test_instance(program_name, test_name, harness_uids[1], time, job_id, build_status,
                                                  submit_status, check_status, outputs, system, events, exit_status)

        # Try with one already in database and the other just needing to be updated.
        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=0, event_name='event')
        cursor.execute(sql)
        db.commit()

        sql = "INSERT INTO {table} (harness_uid, harness_start, harness_tld, " \
              "application, testname, system, next_harness_uid, done) " + \
              "VALUES ({harness_uid}, {harness_start}, {harness_tld}, " \
              "{application}, {testname}, {system}, {next_harness_uid}, {done})" \
                  .format(table=self.test_table, harness_uid=harness_uids[0], harness_start=time, harness_tld='path',
                          application=program_name, testname=test_name, system=system, next_harness_uid=harness_uids[0],
                          done=False)
        cursor.execute(sql)
        db.commit()

        self.assertFalse(self.in_table(self.test_table, **{'harness_uid': harness_uids[0], 'build_status': build_status}))
        self.assertFalse(self.in_table(self.test_table, **{'harness_uid': harness_uids[1]}))
        self.assertFalse(self.in_table(self.test_event_table, **{'event_id': 0}))

        self.init_update_database()
        self.UD.update_test_instances(self.IC.path_to_example_tests)

        self.assertTrue(self.in_table(self.test_table, **{'harness_uid': harness_uids[0], 'build_status': build_status,
                                                          'build_output_text': build_output_text}))
        self.assertTrue(self.in_table(self.test_table, **{'harness_uid': harness_uids[1],
                                                          'build_output_text': build_output_text}))
        self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 0, 'test_id': 0}))
        self.assertTrue(self.in_table(self.test_event_table, **{'event_id': 0, 'test_id': 1}))

    def test_update_tests(self):
        program_names = ['program_1', 'program_2']
        test_names = ['test_alpha', 'test_beta']
        time = '00:00:0300'
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

        instance_count = 0
        new_uids = []
        for program_name in program_names:
            for test_name in test_names:
                for harness_uid in harness_uids:
                    if random() > 0.5 or instance_count == 0:
                        new_uid = program_name + '_' + test_name + '_' + harness_uid

                        instance = self.IC.create_test_instance(program_name, test_name, new_uid, time, job_id,
                                                                build_status, submit_status, check_status, outputs,
                                                                system, events, exit_status)
                        instance_count += 1
                        new_uids.append(new_uid)

        # Try with one already in database and the other just needing to be updated.
        db = self.connector.connect()
        cursor = db.cursor()
        sql = "INSERT INTO {table} (event_uid, event_name) VALUES ({event_uid}, {event_name})" \
            .format(table=self.event_table, event_uid=0, event_name='event')
        cursor.execute(sql)
        db.commit()

        for uid in new_uids:
            self.assertFalse(self.in_table(self.test_table, **{'harness_uid': uid}))

        self.init_update_database(self.IC.path_to_rgt_input)

        for uid in new_uids:
            self.assertTrue(self.in_table(self.test_table, **{'harness_uid': uid}))
