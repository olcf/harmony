from scripts import parse_file
import unittest
import os

class TestErrors(unittest.TestCase):
    def test_syntax_exception(self):
        # Test that if the exception is raised, it is the correct exception.
        # This lambda function raises the exception
        ex = lambda: (_ for _ in ()).throw(parse_file.SyntaxException)
        with self.assertRaises(parse_file.SyntaxException):
            ex()

    def test_syntax_problem(self):
        message = "Problem"
        text = ['text line 0', 'text line 1', 'text line 2', 'text line 3']
        line_nums = [-1, 0]

        for line_num in line_nums:
            ex = parse_file.SyntaxProblem(message=message, line_num=line_num)
            with self.subTest(line_num=line_num):
                self.assertEqual(message, ex.message)
                self.assertEqual(line_num, ex.line_num)

                self.assertIn(message, ex.toString(text))
                if line_num != -1:
                    self.assertIn(text[line_num], ex.toString(text))
                    self.assertIn(str(line_num), ex.toString(text))


def write_to_file(file_path, text):
    with open(file_path, mode='w') as f:
        f.write(text)


class TestParseJobID(unittest.TestCase):
    def setUp(self):
        self.path_to_job_ids = os.path.join(os.getcwd(), 'test_inputs', 'test_job_ids')
        self.parse_job_id = parse_file.ParseJobID().parse_file

    def test_absent_job_id(self):
        file_path = os.path.join(self.path_to_job_ids, 'absent_job_id.txt')
        write_to_file(file_path, "                       \n                  ")

        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    def test_str_job_id(self):
        file_path = os.path.join(self.path_to_job_ids, 'string_job_id.txt')
        write_to_file(file_path, "  testing\n\n\n\n")

        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    def test_negative_job_id(self):
        file_path = os.path.join(self.path_to_job_ids, 'negative_job_id.txt')
        write_to_file(file_path, "                 \n  -1")

        with self.assertRaises(parse_file.SyntaxException):
            self.parse_job_id(file_path)

    def test_good_job_id(self):
        file_path = os.path.join(self.path_to_job_ids, 'good_job_id.txt')
        job_id = 1
        write_to_file(file_path, "\n " + str(job_id))

        self.assertEqual(job_id, self.parse_job_id(file_path))


class TestParseRGTInput(unittest.TestCase):
    def setUp(self):
        self.path_to_rgts = os.path.join(os.getcwd(), 'test_inputs', 'test_rgts')
        self.parse_rgt_input = parse_file.ParseRGTInput().parse_file
        self.PR = parse_file.ParseRGTInput()
        self.path_to_example_tests = os.path.join(os.getcwd(), 'example_test')

    def test_remove_commented(self):
        contents = ['       ',
                    '# Example text',
                    '       # More example text',
                    'something_useful',
                    '',
                    '               useful # not_useful']
        contents = list(enumerate(contents))
        new_contents = self.PR.remove_commented(contents)
        self.assertEqual(2, len(new_contents), msg='There should only be two useful lines.')
        self.assertEqual(3, new_contents[0][0], msg='The first useful line is line 3.')
        self.assertEqual(5, new_contents[1][0], msg='The second useful line is line 5')
        self.assertEqual(contents[3], new_contents[0])
        self.assertEqual('useful', new_contents[1][1])

    def test_split_line(self):
        bad_lines = ['test no equals',
                     'test = too = many equals',
                     '= nothing before',
                     'too much = before',
                     'nothing_after =',
                     'too = much after equals']
        bad_lines = list(enumerate(bad_lines))
        for bad_line in bad_lines:
            with self.assertRaises(parse_file.SyntaxProblem):
                self.PR.split_line(bad_line)

        good_lines = ['path = some/path',
                      'test = fantastic thing']
        good_lines = list(enumerate(good_lines))

        good_line = good_lines[0]
        line_num, line_dic = self.PR.split_line(good_line)
        self.assertEqual(good_line[0], line_num)
        self.assertEqual('path', line_dic['var'])
        self.assertEqual(['some/path'], line_dic['vals'])

        good_line = good_lines[1]
        line_num, line_dic = self.PR.split_line(good_line)
        self.assertEqual(good_line[0], line_num)
        self.assertEqual('test', line_dic['var'])
        self.assertEqual(['fantastic', 'thing'], line_dic['vals'])

    def test_parse_vars(self):
        with self.assertRaises(Exception):
            self.PR.parse_vars([])

        bad_files = [['path_to_tests', []],
                     ['path_to_tests', ['0', '1']],
                     ['path_to_tests', ['0'], 'path_to_tests', ['1']],

                     ['path_to_tests', ['0'], 'test', ['0']],
                     ['path_to_tests', ['0'], 'test', ['0', '1', '2']],

                     ['bad_variable', ['']]]

        for bad_file in bad_files:
            new_bad_file = []
            for i in range(0, len(bad_file), 2):
                new_bad_file.append((i/2, {'var': bad_file[i], 'vals': bad_file[i + 1]}))

            with self.assertRaises(parse_file.SyntaxProblem):
                self.PR.parse_vars(new_bad_file)

        good_files = [['path_to_tests', ['0']],
                      ['path_to_tests', ['0'], 'test', ['good', 'test']],
                      ['path_to_tests', ['0'], 'test', ['good', 'test'], 'test', ['great', 'test']],
                      ['test', ['good', 'test'], 'path_to_tests', ['0']]]
        num_tests = [0, 1, 2, 1]

        for index, good_file in enumerate(good_files):
            new_good_file = []
            for i in range(0, len(good_file), 2):
                new_good_file.append((i/2, {'var': good_file[i], 'vals': good_file[i + 1]}))

            path_to_tests, test_list = self.PR.parse_vars(new_good_file)
            self.assertEqual('0', path_to_tests)
            self.assertEqual(num_tests[index], len(test_list))
            if len(test_list) != 0:
                first_test = test_list[0]
                self.assertEqual('good', first_test['program'])
                self.assertEqual('test', first_test['test'])


    def test_bad_nothing(self):
        file_path = os.path.join(self.path_to_rgts, 'nothing_rgt.txt')
        write_to_file(file_path, "")

        with self.assertRaises(Exception):
            self.parse_rgt_input(file_path)

    def test_bad_no_path(self):
        file_path = os.path.join(self.path_to_rgts, 'bad_no_path_rgt.txt')
        write_to_file(file_path, "test = one two")

        with self.assertRaises(Exception):
            self.parse_rgt_input(file_path)

    def test_good_no_comments_only_path(self):
        file_path = os.path.join(self.path_to_rgts, 'good_no_comments_only_path_rgt.txt')
        write_to_file(file_path, "path_to_tests = " + self.path_to_example_tests)

        path_to_tests, test_list = self.parse_rgt_input(file_path)
        self.assertEqual(self.path_to_example_tests, path_to_tests)
        self.assertEqual(0, len(test_list), msg="Since no tests were written, none should exist.")

    def test_good_no_comments(self):
        file_path = os.path.join(self.path_to_rgts, 'good_no_comments_rgt.txt')
        program_name = 'program_name'
        test_name = 'test_name'
        write_to_file(file_path, "path_to_tests = " + self.path_to_example_tests + "\n"
                      + "test = " + program_name + " " + test_name)

        path_to_tests, test_list = self.parse_rgt_input(file_path)
        self.assertEqual(self.path_to_example_tests, path_to_tests)
        self.assertEqual(1, len(test_list))
        test = test_list[0]
        self.assertIn('program', test.keys())
        self.assertIn('test', test.keys())
        self.assertEqual(program_name, test['program'])
        self.assertEqual(test_name, test['test'])


if __name__ == '__main__':
    unittest.main()
