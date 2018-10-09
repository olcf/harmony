from scripts.notifications.slack_app import slack_commands
import unittest
from unit_tests import get_actual_jobs


class TestStaticFunctions(unittest.TestCase):
    """
    Test functions in slack_commands that do not belong to a class.
    """

    def test_docstring_parameter(self):
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

        self.assertIn(param, has_doc_par.__doc__)
        self.assertNotIn(param, no_doc_par.__doc__)

    def test_is_command(self):
        @slack_commands.is_command()
        def command_1():
            return

        self.assertTrue(hasattr(command_1, 'is_command'))
        self.assertTrue(command_1.is_command)

        @slack_commands.is_command(command=True)
        def command_2():
            return

        self.assertTrue(hasattr(command_2, 'is_command'))
        self.assertTrue(command_2.is_command)

        def not_command_1():
            return

        self.assertFalse(hasattr(not_command_1, 'is_command'))

        @slack_commands.is_command(command=False)
        def not_command_2():
            return

        self.assertTrue(hasattr(not_command_2, 'is_command'))
        self.assertFalse(not_command_2.is_command)

    def test_get_functions(self):
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

        commands = slack_commands.get_functions(function_class)
        self.assertIn('command_1', commands.keys())
        self.assertIn('command_2', commands.keys())
        self.assertNotIn('not_command_1', commands.keys())
        self.assertNotIn('not_command_2', commands.keys())

    def test_make_columns_smaller(self):
        """
        Test if columns are made correctly if the strings in the tuples are smaller than the set column sizes.
        :return:
        """
        tuple_list = [('a', 'test_a', 0), ('b', 'test_b', 1), ('c', 'test_c', 2)]
        col_sizes = [10, 10, 10]
        col_ranges = [0]
        for i in range(len(col_sizes)):
            # Add 1 since there is a space at the end of the column.
            col_ranges.append(col_ranges[i] + col_sizes[i] + 1)

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
        # Expect column sizes to be 1, 26, 1
        tuple_list = [('a', 'test_a', 0), ('b', 'test_b', 1), ('c', 'test_c c c c c c c c c c c', 2)]
        col_sizes = [10, 10, 10]
        col_ranges = [0]
        for i in range(len(col_sizes)):
            # Add 1 since there is a space at the end of the column.
            col_ranges.append(col_ranges[i] + col_sizes[i] + 1)

        columns = slack_commands.make_columns(tuple_list, col_sizes)
        columns = columns.splitlines()

        self.assertEqual(len(tuple_list), len(columns))
        for i in range(len(columns)):
            tup = tuple_list[i]
            with self.subTest(tuple=tup):
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
        self.watch_time = 1
        self.MP = slack_commands.MessageParser(self.watch_time)

    def test_slack_help(self):
        self.assertTrue(self.MP.slack_help.is_command)
        help_response = self.MP.slack_help()

        self.assertIn(self.MP.bot_name, help_response)
        self.assertIn('slack_help', help_response)
        self.assertIn('return', help_response)

    def test_my_jobs(self):
        # Some username that will not occur.
        username = 'abcdefghijklmnopqrstuvwxyz123456789'

        response = self.MP.my_jobs(username)

        self.assertIn(username, response)
        self.assertIn('0 jobs', response)

    def test_all_jobs(self):
        response = self.MP.all_jobs()
        actual_jobs = get_actual_jobs.get_jobs()

        for actual_job in actual_jobs:
            self.assertIn(str(actual_job['jobid']), response)

