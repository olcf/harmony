import copy



class ParseJobID:
    """
    Parse the job_id.txt file that each test has when run.
    """

    def parse_file(self, file_path):
        """
        Parse the input file and get the id for the job.

        :param file_path: (str) Path to 'job_id.txt'
        :return: (int) Id of the job.
        """
        # Open the file and get the text.
        with open(file_path) as file:
            file_contents = [line for line in file]

        # Initially no jobID.
        jobID = None
        # For each line in the file, test if it is an int once the spaces on both sides are removed.
        for l in file_contents:
            # If int then found the jobID.
            try:
                jobID = int(l.strip())
                break
            # Otherwise move to the next line.
            except:
                continue
        # If jobID exists and not negative, return it.
        if jobID is not None and jobID >= 0:
            return jobID
        # Otherwise error.
        elif jobID is None:
            raise SyntaxException("No jobid found in " + file_path)
        else:
            raise SyntaxException("Negative jobid found in " + file_path)


# Class to parse the rgt master input file.
class ParseRGTInput:
    """
    Parse the master rgt input file and get necessary information.
    """
    def parse_file(self, file_path, verbose=False):
        """
        Get the path to tests and the tests from an rgt file.

        :param file_path: (str) Path to rgt.input.master.
        :param verbose: (boolean) Whether to show status.
        :returns: path_to_tests: (str) Path to location of tests in rgt,
                  test_list: (list) List of dictionaries containing test information.
        """
        # Open the file and get the text.
        with open(file_path) as file:
            file_contents = [line for line in file]

        # Copy the contents so that it is easier to debug problems in the file.
        unchanged_contents = copy.deepcopy(file_contents)
        # Enumerate the file_contents so that the problem lines can be referenced to when throwing an error.
        file_contents = list(enumerate(file_contents))

        # Remove all lines that are comments.
        if verbose:
            print("Removing commented lines.")
        file_contents = self.remove_commented(file_contents)

        # Split each line into the variable to be set and the value it is set as.
        if verbose:
            print("Splitting lines.")
        try:
            file_contents = self.split_lines(file_contents)
        # Raise a nicer exception that highlights the problem line.
        except SyntaxProblem as e:
            raise SyntaxException(e.toString(unchanged_contents))

        # Get the values out of the split lines.
        if verbose:
            print("Parsing variables.")
        try:
            path_to_tests, test_list = self.parse_vars(file_contents)
        except SyntaxProblem as e:
            raise SyntaxException(e.toString(unchanged_contents))

        # Return the path to the tests and the list of dictionaries that contain test info.
        return path_to_tests, test_list

    # Remove all lines from the file that start with a '#'.
    def remove_commented(self, file_contents):
        """
        Remove all useless lines from an enumerated file.

        :param file_contents: (list) Enumerated file.
        :return: (list) Enumerated file with useless lines and comments removed.
        """
        # Initially no lines to keep.
        contents = []
        # For each line in file contents check if it has a '#' as it's leftmost non-space character.
        for line_tup in file_contents:
            # Since file contents contains tuples with the line number
            # and the actual contents we need to get the contents.
            line = line_tup[1]
            # Remove everything after first '#'.
            if line.find('#') != -1:
                line = line[:line.find('#')]
            # If the line actually has something in it then there exists important text.
            # If it has nothing then do not add it to the contents.
            if len(line.strip()) > 0:
                contents.append((line_tup[0], line.strip()))
        # Return the important contents.
        return contents

    def split_lines(self, file_contents):
        """
        Split lines in a file into the variable to be set and the contents to set it as.

        :param file_contents: (list) Enumerated file without comments.
        :return: (list) Enumerated list of dictionaries containing variable and values.
        """
        # Initially no contents.
        contents = []
        # For each (line_num, contents) in the file_contents, try to split it.
        for line_tup in file_contents:
            line_num, line_dic = self.split_line(line_tup)
            # Add it to the list along with it's line number.
            contents.append((line_num, line_dic))
        # Return the list of dictionaries.
        return contents

    def split_line(self, line_tup):
        """
        Split a single line into it's variable and values.

        :param line_tup: (tuple) Tuple containing line number and contents.
        :returns: line_num: (int) Line that was edited.
                  line_dic: (dic) Dictionary containing 'var' (variable) and 'vals' (values).
        """
        # Get the actual contents.
        line = line_tup[1]
        # Get the corresponding line number.
        line_num = line_tup[0]
        # Split the line by the '=' sign. There should only be one and each line needs one.
        line = line.split('=')
        if len(line) < 2:
            raise SyntaxProblem(message="Not enough '='.", line_num=line_num)
        elif len(line) > 2:
            raise SyntaxProblem(message="Too many '='.", line_num=line_num)
        # Now split it by the spaces.
        line = [l.split() for l in line]
        # If there is nothing befor the '=' then there is a problem.
        if len(line[0]) == 0:
            raise SyntaxProblem(message="Nothing before '='.", line_num=line_num)
        # If there are multiple things before the '=' then we have a problem.
        elif len(line[0]) > 1:
            raise SyntaxProblem(message="Too many space separated items before '='.", line_num=line_num)
        # There needs to be something after the '='.
        if len(line[1]) == 0:
            raise SyntaxProblem(message="Nothing after '='.", line_num=line_num)
        # Anything more than two is too much.
        elif len(line[1]) > 2:
            raise SyntaxProblem(message="Too many space separated items after '='.", line_num=line_num)
        # Create a dictionary containing the string for the variable and a list containing the value(s).
        line_dic = {"var": line[0][0], "vals": line[1]}
        return line_num, line_dic

    def parse_vars(self, file_contents):
        """
        Parse a list of dictionaries containing variables and values.

        :param file_contents: File with lines split into dictionaries.
        :returns: path_to_tests: (str) Path to where tests are stored.
                  test_list: (list) List of dictionaries containing the program and test name.
        """
        # Initially there are no tests.
        test_list = []
        # Initially no path.
        path_to_tests = None
        # For each enumerated tuple in the file contents.
        for line_tup in file_contents:
            # Get the line number from the tuple.
            line_num = line_tup[0]
            # Get the variable name from the dictionary in the tuple.
            var = line_tup[1]["var"]
            # Get the values from the dictionary in the tuple.
            vals = line_tup[1]["vals"]

            # If the lowercase variable is 'path_to_tests' then we have found the path.
            if var.lower() == "path_to_tests":
                if len(vals) == 0:
                    raise SyntaxProblem(message="No path to tests.", line_num=line_num)
                elif len(vals) > 1 or path_to_tests is not None:
                    raise SyntaxProblem(message="Too many paths to tests.", line_num=line_num)
                path_to_tests = vals[0]
            # If the lowercase variable is 'test' then we have found a test.
            elif var.lower() == "test":
                if len(vals) < 2:
                    raise SyntaxProblem(message="Need both program name and test name.", line_num=line_num)
                elif len(vals) > 2:
                    raise SyntaxProblem(message="Too many values after test. Only need program name and test name.", line_num=line_num)
                # Append a dictionary to the list of tests.
                test_list.append({"program": vals[0], "test": vals[1]})
            # If it is neither of the above then there is a problem.
            else:
                raise SyntaxProblem(message="Incorrect variable to set. Should be either 'path_to_tests' or 'test'.", line_num=line_num)

        # If we did not find a path then there is a problem.
        if path_to_tests is None:
            raise Exception("No path to tests found.")

        # Return the path and the list of tests.
        return path_to_tests, test_list


class SyntaxProblem(Exception):
    """
    This class contains the required info for any syntax error in the rgt input file.
    """
    def __init__(self, message, line_num=-1):
        """
        Initialize the error.

        :param message: (str) Message of what was the problem with the line.
        :param line_num: (int) Line number that was the problem.
        """
        # Initialize this as an Exception.
        super().__init__(message)
        # Set the message.
        self.message = message
        # Set the line number.
        self.line_num = line_num

    def toString(self, unchanged_contents):
        """
        Change the class into a string that also shows the problem line.

        :param unchanged_contents: (list) Contents of initial file.
        :return: new_message: Correct error message.
        """
        # Create a new message with the original string.
        new_message = self.message
        # If there is a line number then add information about the line.
        if self.line_num != -1:
            new_message += "\nline " + str(self.line_num) + ":\t" + unchanged_contents[self.line_num]
        return new_message


# This class is used to transform a SyntaxError into a single exception.
class SyntaxException(Exception):
    pass


if __name__ == '__main__':
    # Set the paths.
    rgtin_path = "/Users/cameronkuchta/Documents/GitHub/harmony/sample_inputs/rgt.input.master"
    job_id_path = "/Users/cameronkuchta/Documents/GitHub/harmony/sample_inputs/sample_run/GTC4/test_0001node/Status/123456789.0123/job_id.txt"
    # Create the classes.
    parseID = ParseJobID()
    parsergt = ParseRGTInput()
    # Print the parsed file.
    print(parsergt.parse_file(rgtin_path))
