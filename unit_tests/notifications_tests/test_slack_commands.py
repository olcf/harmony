from scripts.notifications.slack_app import slack_commands
import unittest
from unit_tests import get_actual_jobs


class TestStaticFunctions(unittest.TestCase):
    """
    Test functions in slack_commands that do not belong to a class.
    """

    def test_docstring_parameter(self):
        """
        Test if a docstring contains the correct info.
        :return:
        """

        # Initialize what the docstring should contain.
        param = "test_test_test"

        @slack_commands.docstring_parameter(par=param)
        def has_doc_par():
            """
            This is my doc_string. I contain {par}.

            :return:
            """
            return

        def no_doc_par():
            """
            This is my doc_string. I don't contain {par}.

            :return:
            """
            return

        # Check that one function has the variable while the other does not.
        self.assertIn(param, has_doc_par.__doc__)
        self.assertNotIn(param, no_doc_par.__doc__)

    def test_is_command(self):
        """
        Test if functions can be correctly labeled as slack commands.
        :return:
        """

        # Initialize function that is a command.
        @slack_commands.is_command()
        def command_1():
            return

        self.assertTrue(hasattr(command_1, 'is_command'))
        self.assertTrue(command_1.is_command)

        # Initialize in a different fashion.
        @slack_commands.is_command(command=True)
        def command_2():
            return

        self.assertTrue(hasattr(command_2, 'is_command'))
        self.assertTrue(command_2.is_command)

        # Initialize a function that is not a command.
        def not_command_1():
            return

        self.assertFalse(hasattr(not_command_1, 'is_command'))

        # Initialize a function that is not a command a different way.
        @slack_commands.is_command(command=False)
        def not_command_2():
            return

        self.assertTrue(hasattr(not_command_2, 'is_command'))
        self.assertFalse(not_command_2.is_command)

    def test_get_functions(self):
        """
        Test if slack commands can be parsed from a class.
        :return:
        """

        # Initialize the class.
        class function_class():
            @slack_commands.is_command()
            def command_1(self):
                return

            @slack_commands.is_command(command=True)
            def command_2(self):
                return

            def not_command_1(self):
                return

            @slack_commands.is_command(command=False)
            def not_command_2(self):
                return

        # Get slack commands and check that the correct commands are in the dictionary.
        commands = slack_commands.get_functions(function_class)
        self.assertIn('command_1', commands.keys())
        self.assertIn('command_2', commands.keys())
        self.assertNotIn('not_command_1', commands.keys())
        self.assertNotIn('not_command_2', commands.keys())

    def test_maximize_col_sizes_single(self):
        """
        Test if a list containing one tuple can create the correct column sizes.
        :return:
        """

        # Set up the initial tuple and the column sizes set and expected.
        single_tuple = [('a', 'test_a', '0')]
        col_sizes = [1, 1, 1]
        expected_col_sizes = [1, 6, 1]

        # Get the new column sizes and check that they are what is expected.
        new_col_sizes = slack_commands.maximize_col_sizes(single_tuple, col_sizes)
        correct_cols = [0, 2]
        for i in range(len(col_sizes)):
            with self.subTest(column=i, expected=expected_col_sizes, actual=new_col_sizes):
                if i in correct_cols:
                    self.assertEqual(col_sizes[i], new_col_sizes[i])
                else:
                    self.assertNotEqual(col_sizes[i], new_col_sizes[i])
                    self.assertEqual(expected_col_sizes[i], new_col_sizes[i])

    def test_maximize_col_sizes_multiple(self):
        """
        Try the same test as above but with multiple tuples.
        :return:
        """
        single_tuple = [('a', 't_a', '0'), ('b', 'test_b', '1')]
        col_sizes = [1, 1, 1]
        expected_col_sizes = [1, 6, 1]

        new_col_sizes = slack_commands.maximize_col_sizes(single_tuple, col_sizes)
        correct_cols = [0, 2]
        for i in range(len(col_sizes)):
            with self.subTest(column=i, expected=expected_col_sizes, actual=new_col_sizes):
                if i in correct_cols:
                    self.assertEqual(col_sizes[i], new_col_sizes[i])
                else:
                    self.assertNotEqual(col_sizes[i], new_col_sizes[i])
                    self.assertEqual(expected_col_sizes[i], new_col_sizes[i])

    def test_make_columns_smaller(self):
        """
        Test if columns are made correctly if the strings in the tuples are smaller than the set column sizes.
        :return:
        """
        # Create a list of tuples.
        tuple_list = [('a', 'test_a', 0), ('b', 'test_b', 1), ('c', 'test_c', 2)]
        # Set the column sizes larger than what is needed.
        col_sizes = [10, 10, 10]
        col_ranges = [0]
        # Get the ranges where we expect the text to be.
        for i in range(len(col_sizes)):
            # Add 1 since there is a space at the end of the column.
            col_ranges.append(col_ranges[i] + col_sizes[i] + 1)

        # Create the columns and check that the columns are created correctly.
        columns = slack_commands.make_columns(tuple_list, col_sizes)
        columns = columns.splitlines()

        self.assertEqual(len(tuple_list), len(columns))
        for i in range(len(columns)):
            with self.subTest(tuple=tuple_list[i]):
                for j in range(len(tuple_list[i])):
                    self.assertIn(str(tuple_list[i][j]), columns[i][col_ranges[j]:col_ranges[j+1]])

    def test_make_columns_bigger(self):
        """
        Test if columns are made correctly if some of the strings in the tuples are bigger than the set column sizes.
        :return:
        """
        # Create the columns and sizes.
        # Expect maximum needed column sizes to be 1, 26, 1
        tuple_list = [('a', 'test_a', 0), ('b', 'long_name_indeed', 1), ('c', 'test_c c c c c c c c c c c', 2)]
        col_sizes = [10, 10, 10]
        col_ranges = [0]
        for i in range(len(col_sizes)):
            # Add 1 since there is a space at the end of the column.
            col_ranges.append(col_ranges[i] + col_sizes[i] + 1)

        # Create the columns and check that the necessary values are in the correct slots or not, depending on
        # how far into the tuple it is.
        columns = slack_commands.make_columns(tuple_list, col_sizes)
        columns = columns.splitlines()

        self.assertEqual(len(tuple_list), len(columns))
        for i in range(len(columns)):
            tup = tuple_list[i]
            with self.subTest(tuple=tup, line=columns[i]):
                for j in range(len(tup)):
                    # The first column should still be correct.
                    if j == 0:
                        self.assertIn(str(tup[j]), columns[i][col_ranges[j]:col_ranges[j+1]])
                    elif j == 1 and len(tup[j]) <= col_sizes[j]:
                        self.assertIn(str(tup[j]), columns[i][col_ranges[j]:col_ranges[j+1]])
                    # The others should be offset.
                    else:
                        self.assertNotIn(str(tup[j]), columns[i][col_ranges[j]:col_ranges[j+1]])


class TestMessageParser(unittest.TestCase):
    """
    Class to test the MessageParser class in slack_commands.
    """

    def setUp(self):
        """
        Set up to the necessary variables for testing the message parser.
        :return:
        """
        self.watch_time = 1
        self.MP = slack_commands.MessageParser(self.watch_time)

    def test_slack_help(self):
        """
        Test if the correct help message is returned when called.
        :return:
        """
        self.assertTrue(self.MP.slack_help.is_command)
        help_response = self.MP.slack_help()

        self.assertIn(self.MP.bot_name, help_response)
        self.assertIn('slack_help', help_response)
        self.assertIn('return', help_response)

    def test_my_jobs(self):
        """
        Test if the message parser can get all jobs from some random username.
        :return:
        """
        # Some username that will not occur.
        username = 'abcdefghijklmnopqrstuvwxyz123456789'

        response = self.MP.my_jobs(username)

        self.assertIn(username, response)
        self.assertIn('0 jobs', response)

    def test_all_jobs(self):
        """
        Test if the parser can get all the jobs from lsf.
        :return:
        """
        response = self.MP.all_jobs()
        actual_jobs = get_actual_jobs.get_jobs()

        for actual_job in actual_jobs:
            self.assertIn(str(actual_job['jobid']), response)

