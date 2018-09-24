import unittest
import os
from scripts import test_status

class TestTestStatus(unittest.TestCase):
    def setUp(self):
        self.notifier = lambda message: message
        self.path_to_tests = os.path.join(os.path.dirname(__file__), 'test_inputs', 'example_test')
        self.path_to_rgts = os.path.join(os.path.dirname(__file__), 'test_inputs', 'rgts_for_test_status')

    def test_get_test_directories(self):
        test_list = [{'program': 'program_name', 'test':'test_name'}]
        test_path_list = test_status.get_test_directories(self.path_to_tests, test_list)

        self.assertEqual(1, len(test_path_list))
        self.assertTrue(os.path.exists(test_path_list[0]))

    def write_to_file(self, file_path, text):
        with open(file_path, mode='w') as f:
            f.write(text)

    def test_check_no_jobs(self):
        text = 'path_to_tests = ' + self.path_to_tests
        file_path = os.path.join(self.path_to_rgts, 'no_jobs_rgt.txt')
        self.write_to_file(file_path, text)

        notification = test_status.check_tests(file_path, notifier=self.notifier)
        # The notification is nothing if there are no missing tests.
        self.assertIsNone(notification)

    def test_check_nonexistant_job(self):
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = imaginary_program fantasy_test"
        file_path = os.path.join(self.path_to_rgts, 'fake_job_rgt.txt')
        self.write_to_file(file_path, text)

        notification = test_status.check_tests(file_path, notifier=self.notifier)
        self.assertIn('exist', notification)
        self.assertNotIn('queue', notification)
        self.assertIn('imaginary_program', notification)
        self.assertIn('fantasy_test', notification)

    def test_check_nonexistant_jobs(self):
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = imaginary_program fantasy_test" + "\n" \
               + "test = unicorn_program chimera_test"
        file_path = os.path.join(self.path_to_rgts, 'fake_jobs_rgt.txt')
        self.write_to_file(file_path, text)

        notification = test_status.check_tests(file_path, notifier=self.notifier)
        self.assertIn('exist', notification)
        self.assertNotIn('queue', notification)
        self.assertIn('imaginary_program', notification)
        self.assertIn('fantasy_test', notification)

    def test_check_unqueued_job(self):
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = program_name test_name"
        file_path = os.path.join(self.path_to_rgts, 'unqueued_job_rgt.txt')
        self.write_to_file(file_path, text)

        notification = test_status.check_tests(file_path, notifier=self.notifier)
        self.assertIn('queue', notification)
        self.assertNotIn('exist', notification)
        self.assertIn('program_name', notification)
        self.assertIn('test_name', notification)

if __name__ == '__main__':
    unittest.main()
