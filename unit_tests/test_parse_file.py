from scripts import parse_file
import unittest
import os

class TestErrors(unittest.TestCase):
    # Test the SyntaxException class.
    def test_syntax_exception(self):
        # Test that if the exception is raised, it is the correct exception.
        # This lambda function raises the exception.
        ex = lambda: (_ for _ in ()).throw(parse_file.SyntaxException)\
        # Assert that the exception is raised.
        with self.assertRaises(parse_file.SyntaxException):
            ex()

    # Test the SyntaxProblem class.
    def test_syntax_problem(self):
        # Create a message.
        message = "Problem"
        # Create a fake file to show that correct line is shown.
        text = ['text line 0', 'text line 1', 'text line 2', 'text line 3']
        # -1 means no line from file. 0 means first line.
        line_nums = [-1, 0]

        # For each of those lines try to make a SyntaxProblem.
        for line_num in line_nums:
            # Lambda function to raise problem with parameters set.
            ex = parse_file.SyntaxProblem(message=message, line_num=line_num)
            # Subtest for each line number.
            with self.subTest(line_num=line_num):
                # Assert that the same message is stored as was input.
                self.assertEqual(message, ex.message)
                # Assert that the correct line number was stored.
                self.assertEqual(line_num, ex.line_num)

                # Assert that the message is in the error string.
                self.assertIn(message, ex.toString(text))
                # If a line number was chosen, test that the correct text is there and the line number.
                if line_num != -1:
                    self.assertIn(text[line_num], ex.toString(text))
                    self.assertIn(str(line_num), ex.toString(text))


# Function to write some text to some file.
def write_to_file(file_path, text):
    with open(file_path, mode='w+') as f:
        f.write(text)


class TestParseJobID(unittest.TestCase):
    # Setup a path to job ids and a parse jod id variable for easier writing/parsing.
    def setUp(self):
        self.path_to_job_ids = os.path.join(os.path.dirname(__file__), 'test_inputs', 'test_job_ids')
        self.parse_job_id = parse_file.ParseJobID().parse_file

    # Test that trying to read a file without anything errors.
    def test_absent_job_id(self):
        # Create the path to the file.
        file_path = os.path.join(self.path_to_job_ids, 'absent_job_id.txt')
        # Empty text to write to file.
        write_to_file(file_path, "                       \n                  ")

        # Make sure it raises an exception.
        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    # Test that a job_id.txt with a string and not an integer errors.
    def test_str_job_id(self):
        # Create path.
        file_path = os.path.join(self.path_to_job_ids, 'string_job_id.txt')
        # Write string and some empty lines to file.
        write_to_file(file_path, "  testing\n\n\n\n")

        # Test that the error occurred when reading.
        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    # If the file contains a negative integer, that is an invalid id.
    def test_negative_job_id(self):
        # Create path.
        file_path = os.path.join(self.path_to_job_ids, 'negative_job_id.txt')
        # Write '-1' to file.
        write_to_file(file_path, "                 \n  -1")

        # Assert that the exception was raised.
        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    # Test that if a good job_id.txt was entered, the correct id was returned.
    def test_good_job_id(self):
        # Create path.
        file_path = os.path.join(self.path_to_job_ids, 'good_job_id.txt')
        # Set job id.
        job_id = 1
        # Write id to file.
        write_to_file(file_path, "\n " + str(job_id))

        # Assert that the correct id was returned.
        self.assertEqual(job_id, self.parse_job_id(file_path))


class TestParseRGTInput(unittest.TestCase):
    # Setup paths to files and variables for common calls.
    def setUp(self):
        self.path_to_rgts = os.path.join(os.path.dirname(__file__), 'test_inputs', 'test_rgts')
        self.parse_rgt_input = parse_file.ParseRGTInput().parse_file
        self.PR = parse_file.ParseRGTInput()
        self.path_to_example_tests = os.path.join(os.getcwd(), 'example_test')

    # Test if all commented/empty lines and line parts are removed.
    def test_remove_commented(self):
        # Create the file.
        contents = ['       ',
                    '# Example text',
                    '       # More example text',
                    'something_useful',
                    '',
                    '               useful # not_useful']
        # Enumberate the file so we keep line numbers.
        contents = list(enumerate(contents))
        # Remove all commented lines.
        new_contents = self.PR.remove_commented(contents)
        # Only two lines should remain.
        self.assertEqual(2, len(new_contents), msg='There should only be two useful lines.')
        # Assert that correct line numbers are still there.
        self.assertEqual(3, new_contents[0][0], msg='The first useful line is line 3.')
        self.assertEqual(5, new_contents[1][0], msg='The second useful line is line 5')
        # Assert that the important parts of the lines are there.
        self.assertEqual(contents[3], new_contents[0])
        self.assertEqual('useful', new_contents[1][1])

    # Test that lines are split correctly and error correctly.
    def test_split_line(self):
        # Create example bad lines.
        bad_lines = ['test no equals',
                     'test = too = many equals',
                     '= nothing before',
                     'too much = before',
                     'nothing_after =',
                     'too = much after equals']
        # Enumerate to keep track of line number.
        bad_lines = list(enumerate(bad_lines))
        # For each of the bad lines, assert that it has a problem when splitting.
        for bad_line in bad_lines:
            with self.assertRaises(parse_file.SyntaxProblem):
                self.PR.split_line(bad_line)

        # Create example good lines and enumerate for line numbers.
        good_lines = ['path = some/path',
                      'test = fantastic thing']
        good_lines = list(enumerate(good_lines))

        # Make sure the first line has the correct results.
        good_line = good_lines[0]
        line_num, line_dic = self.PR.split_line(good_line)
        self.assertEqual(good_line[0], line_num)
        self.assertEqual('path', line_dic['var'])
        self.assertEqual(['some/path'], line_dic['vals'])

        # Make sure that the second line has the correct results.
        good_line = good_lines[1]
        line_num, line_dic = self.PR.split_line(good_line)
        self.assertEqual(good_line[0], line_num)
        self.assertEqual('test', line_dic['var'])
        self.assertEqual(['fantastic', 'thing'], line_dic['vals'])

    # Test that variables can be parsed from a file.
    def test_parse_vars(self):
        # Assert that an empty file is a problem.
        with self.assertRaises(Exception):
            self.PR.parse_vars([])

        # Create example bad files.
        bad_files = [['path_to_tests', []],
                     ['path_to_tests', ['0', '1']],
                     ['path_to_tests', ['0'], 'path_to_tests', ['1']],

                     ['path_to_tests', ['0'], 'test', ['0']],
                     ['path_to_tests', ['0'], 'test', ['0', '1', '2']],

                     ['bad_variable', ['']]]

        # For each file, make sure it errors.
        for bad_file in bad_files:
            # Create enumerated file.
            new_bad_file = []
            for i in range(0, len(bad_file), 2):
                new_bad_file.append((i/2, {'var': bad_file[i], 'vals': bad_file[i + 1]}))

            # Assert that error is raised.
            with self.assertRaises(parse_file.SyntaxProblem):
                self.PR.parse_vars(new_bad_file)

        # Create example good files.
        good_files = [['path_to_tests', ['0']],
                      ['path_to_tests', ['0'], 'test', ['good', 'test']],
                      ['path_to_tests', ['0'], 'test', ['good', 'test'], 'test', ['great', 'test']],
                      ['test', ['good', 'test'], 'path_to_tests', ['0']]]
        # Store the number of tests in each file.
        num_tests = [0, 1, 2, 1]

        # For each of the good files, make sure correct values are returned.
        for index, good_file in enumerate(good_files):
            # Enumerate the good file.
            new_good_file = []
            for i in range(0, len(good_file), 2):
                new_good_file.append((i/2, {'var': good_file[i], 'vals': good_file[i + 1]}))

            # Get path and test list.
            path_to_tests, test_list = self.PR.parse_vars(new_good_file)
            # Since all paths to tests are '0', make sure that is what is found.
            self.assertEqual('0', path_to_tests)
            # Test that the number of tests match up.
            self.assertEqual(num_tests[index], len(test_list))
            # Make sure that the first test is correct.
            if len(test_list) != 0:
                first_test = test_list[0]
                self.assertEqual('good', first_test['program'])
                self.assertEqual('test', first_test['test'])

    # Test that an error occurs if the file is empty.
    def test_bad_nothing(self):
        file_path = os.path.join(self.path_to_rgts, 'nothing_rgt.txt')
        write_to_file(file_path, "")

        with self.assertRaises(Exception):
            self.parse_rgt_input(file_path)

    # Test that an error occurs if the path is bad.
    def test_bad_no_path(self):
        file_path = os.path.join(self.path_to_rgts, 'bad_no_path_rgt.txt')
        write_to_file(file_path, "test = one two")

        with self.assertRaises(Exception):
            self.parse_rgt_input(file_path)

    # Test that a file is good as long as the path exists.
    def test_good_no_comments_only_path(self):
        file_path = os.path.join(self.path_to_rgts, 'good_no_comments_only_path_rgt.txt')
        write_to_file(file_path, "path_to_tests = " + self.path_to_example_tests)

        # Get path and list of tests.
        path_to_tests, test_list = self.parse_rgt_input(file_path)
        # Make sure path is correct.
        self.assertEqual(self.path_to_example_tests, path_to_tests)
        # Make sure that there are no tests found.
        self.assertEqual(0, len(test_list), msg="Since no tests were written, none should exist.")

    # Test that a file that contains tests is correct.
    def test_good_no_comments(self):
        # Create the file.
        file_path = os.path.join(self.path_to_rgts, 'good_no_comments_rgt.txt')
        program_name = 'program_name'
        test_name = 'test_name'
        write_to_file(file_path, "path_to_tests = " + self.path_to_example_tests + "\n"
                      + "test = " + program_name + " " + test_name)

        # Get path and list of tests.
        path_to_tests, test_list = self.parse_rgt_input(file_path)
        # Assert that the path is correct.
        self.assertEqual(self.path_to_example_tests, path_to_tests)
        # Assert that correct number of tests found.
        self.assertEqual(1, len(test_list))

        # Assert that correct items in test list.
        test = test_list[0]
        self.assertIn('program', test.keys())
        self.assertIn('test', test.keys())
        self.assertEqual(program_name, test['program'])
        self.assertEqual(test_name, test['test'])

    # Test that a file that contains tests is correct.
    def test_good_comments(self):
        # Create the file.
        file_path = os.path.join(self.path_to_rgts, 'good_comments_rgt.txt')
        program_name = 'program_name'
        test_name = 'test_name'
        write_to_file(file_path, "path_to_tests = " + self.path_to_example_tests + "\n"
                      + " # Commented text" + "\n"
                      + "           # test = commented test" + "\n"
                      + "test = " + program_name + " " + test_name)

        # Get path and list of tests.
        path_to_tests, test_list = self.parse_rgt_input(file_path)
        # Assert that the path is correct.
        self.assertEqual(self.path_to_example_tests, path_to_tests)
        # Assert that correct number of tests found.
        self.assertEqual(1, len(test_list))

        # Assert that correct items in test list.
        test = test_list[0]
        self.assertIn('program', test.keys())
        self.assertIn('test', test.keys())
        self.assertEqual(program_name, test['program'])
        self.assertEqual(test_name, test['test'])


if __name__ == '__main__':
    unittest.main()
