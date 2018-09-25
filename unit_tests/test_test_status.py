import unittest
import os
from scripts import test_status

class TestTestStatus(unittest.TestCase):
    # Setup a variables for use later on.
    def setUp(self):
        # Notifier so it does not try to send to slack and instead just returns the message.
        self.notifier = lambda message: message
        # Set paths.
        self.path_to_tests = os.path.join(os.path.dirname(__file__), 'test_inputs', 'example_test')
        self.path_to_rgts = os.path.join(os.path.dirname(__file__), 'test_inputs', 'rgts_for_test_status')

    # Test is the path to a test can be found.
    def test_get_test_directories(self):
        # List of tests.
        test_list = [{'program': 'program_name', 'test':'test_name'}]
        # Get list of paths.
        test_path_list = test_status.get_test_directories(self.path_to_tests, test_list)

        # Make sure one path was found.
        self.assertEqual(1, len(test_path_list))
        # Assert that the path exists.
        self.assertTrue(os.path.exists(test_path_list[0]))

    # Function to write to a file.
    def write_to_file(self, file_path, text):
        with open(file_path, mode='w+') as f:
            f.write(text)

    # Test is a file with no tests but with path has no problem.
    def test_check_no_jobs(self):
        # Set path to tests.
        text = 'path_to_tests = ' + self.path_to_tests
        # Set the path to where the rgt file will be written.
        file_path = os.path.join(self.path_to_rgts, 'no_jobs_rgt.txt')
        # Create the file.
        self.write_to_file(file_path, text)

        # Get the notification that would have been sent.
        notification = test_status.check_tests(file_path, notifier=self.notifier)
        # The notification is nothing if there are no missing tests.
        self.assertIsNone(notification)

    # Test that an error occurs if the specified test does not exist.
    def test_check_nonexistant_job(self):
        # Create the file text.
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = imaginary_program fantasy_test"
        # Set the file path.
        file_path = os.path.join(self.path_to_rgts, 'fake_job_rgt.txt')
        # Create the file.
        self.write_to_file(file_path, text)

        # Get the notification.
        notification = test_status.check_tests(file_path, notifier=self.notifier)
        # Assert that correct words are in the notification.
        self.assertIn('exist', notification)
        self.assertNotIn('queue', notification)
        self.assertIn('imaginary_program', notification)
        self.assertIn('fantasy_test', notification)

    # Test that if there are multiple fake jobs, neither exist.
    def test_check_nonexistant_jobs(self):
        # Create file text with multiple fake jobs.
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = imaginary_program fantasy_test" + "\n" \
               + "test = unicorn_program chimera_test"
        # Set the path to the file.
        file_path = os.path.join(self.path_to_rgts, 'fake_jobs_rgt.txt')
        # Create the file.
        self.write_to_file(file_path, text)

        # Get the notification.
        notification = test_status.check_tests(file_path, notifier=self.notifier)
        self.assertIn('exist', notification)
        self.assertNotIn('queue', notification)
        self.assertIn('imaginary_program', notification)
        self.assertIn('fantasy_test', notification)
        self.assertIn('unicorn_program', notification)
        self.assertIn('chimera_test', notification)

    # Test that a test that exists but is unqueued raises an error.
    def test_check_unqueued_job(self):
        # Set the file text.
        text = 'path_to_tests = ' + self.path_to_tests + "\n test = program_name test_name"
        # Set the file path.
        file_path = os.path.join(self.path_to_rgts, 'unqueued_job_rgt.txt')
        # Create the file.
        self.write_to_file(file_path, text)

        # Get the notification.
        notification = test_status.check_tests(file_path, notifier=self.notifier)
        # Assert that correct words are in notification.
        self.assertIn('queue', notification)
        self.assertNotIn('exist', notification)
        self.assertIn('program_name', notification)
        self.assertIn('test_name', notification)

    # Test that a test that exists but is unqueued raises an error.
    def test_check_unqueued_and_nonexistant_job(self):
        # Set the file text.
        text = 'path_to_tests = ' + self.path_to_tests + "\n" +\
               " test = program_name test_name" + "\n" +\
               "test = imaginary_program fantasy_test"
        # Set the file path.
        file_path = os.path.join(self.path_to_rgts, 'unqueued_and_nonexistant_job_rgt.txt')
        # Create the file.
        self.write_to_file(file_path, text)

        # Get the notification.
        notification = test_status.check_tests(file_path, notifier=self.notifier)
        # Assert that correct words are in notification.
        self.assertIn('queue', notification)
        self.assertIn('exist', notification)
        self.assertIn('program_name', notification)
        self.assertIn('test_name', notification)
        self.assertIn('imaginary_program', notification)
        self.assertIn('fantasy_test', notification)

if __name__ == '__main__':
    unittest.main()
