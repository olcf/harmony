import unittest
import os
from scripts import test_status

class TestTestStatus(unittest.TestCase):
    """
    Test the test_status.py file.
    """

    def setUp(self):
        """
        Setup variables for use later on.
        """
        # Notifier so it does not try to send to slack and instead just returns the message.
        self.notifier = lambda message: message
        # Set paths.
        self.path_to_tests = os.path.join(os.path.dirname(__file__), 'test_inputs', 'example_test')
        self.path_to_rgts = os.path.join(os.path.dirname(__file__), 'test_inputs', 'rgts_for_test_status')

    def test_get_test_directories(self):
        """
        Test if the path to a test can be found.
        """
        # List of tests.
        test_list = [{'program': 'program_name', 'test':'test_name'}]
        # Get list of paths.
        test_path_list = test_status.get_test_directories(self.path_to_tests, test_list)

        # Make sure one path was found.
        self.assertEqual(1, len(test_path_list))
        # Assert that the path exists.
        self.assertTrue(os.path.exists(test_path_list[0]))

    def write_to_file(self, file_path, text):
        """
        Write some text to some file.

        :param file_path: (str) Path to file to write.
        :param text: (str) Text to write to file.
        """
        with open(file_path, mode='w+') as f:
            f.write(text)

    def test_check_no_jobs(self):
        """
        Test is a file with no tests but with path has no problem.
        """
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

    def test_check_nonexistant_job(self):
        """
        Test that an error occurs if the specified test does not exist.
        """
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

    def test_check_nonexistant_jobs(self):
        """
        Test that if there are multiple fake jobs, neither exist.
        """
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

    def test_check_unqueued_job(self):
        """
        Test that a test that exists but is unqueued raises an error.
        """
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

    def test_check_unqueued_and_nonexistant_job(self):
        """
        Test that a test that exists but is unqueued raises an error.
        """
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
