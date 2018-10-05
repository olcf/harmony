from scripts.notifications.slack_app import slack_commands
import unittest

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
        @slack_commands.is_command
        def command_1():
            return

        self.assertTrue(hasattr(command_1, 'is_command'))
        self.assertTrue(command_1.is_command)

        @slack_commands.is_command(slack_command=True)
        def command_2():
            return

        self.assertTrue(hasattr(command_2, 'is_command'))
        self.assertTrue(command_2.is_command)

        def not_command_1():
            return

        self.assertFalse(hasattr(not_command_1, 'is_command'))

        @slack_commands.is_command(slack_command=False)
        def not_command_2():
            return

        self.assertTrue(hasattr(not_command_2, 'is_command'))
        self.assertFalse(not_command_2.is_command)

    def test_get_functions(self):
        class function_class():
            @slack_commands.is_command
            def command_1(self):
                return

            @slack_commands.is_command(slack_command=True)
            def command_2(self):
                return

            def not_command_1(self):
                return

            @slack_commands.is_command(slack_command=False)
            def not_command_2(self):
                return

        commands = slack_commands.get_functions(function_class)
        self.assertIn('command_1', commands.keys())
        self.assertIn('command_2', commands.keys())
        self.assertNotIn('not_command_1', commands.keys())
        self.assertNotIn('not_command_2', commands.keys())

    def test_make_columns(self):
        tuple_list = [('a', 'test_a', 0), ('b', 'test_b', 1), ('c', 'test_c', 2)]
        col_sizes = [10, 10, 10]
        col_ranges = [0]
        for i in range(len(col_sizes)):
            col_ranges.append(col_ranges[i] + col_sizes[i])

        columns = slack_commands.make_columns(tuple_list, col_sizes)
        columns = columns.splitlines()

        self.assertEqual(len(tuple_list), len(columns))
        for i in range(len(columns)):
            with self.subTest(tuple=tuple_list[i]):
                for j in range(len(tuple_list[i])):
                    self.assertIn(str(tuple_list[i][j]), columns[i][col_ranges[j]:col_ranges[j+1]])


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
