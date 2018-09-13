import copy

class ParseJobID:
    def parse_file(self, file_path):
        with open(file_path) as file:
            file_contents = [line for line in file]

        jobID = None
        for l in file_contents:
            try:
                jobID = int(l.strip())
                break
            except:
                continue
        if jobID is not None:
            return jobID
        else:
            raise Exception("No jobid found in " + file_path)


class ParseRGTInput:
    def parse_file(self, file_path, verbose=False):
        with open(file_path) as file:
            file_contents = [line for line in file]

        unchanged_contents = copy.deepcopy(file_contents)
        # This is used to raise errors and find what line is the problem.
        file_contents = list(enumerate(file_contents))
        if verbose:
            print("Removing commented lines.")
        file_contents = self.remove_commented(file_contents)

        if verbose:
            print("Splitting lines.")
        try:
            file_contents = self.split_lines(file_contents)
        except SyntaxError as e:
            raise Exception(e.toString(unchanged_contents))

        if verbose:
            print("Parsing variables.")
        try:
            path_to_tests, test_list = self.parse_vars(file_contents)
        except SyntaxError as e:
            raise Exception(e.toString(unchanged_contents))

        return path_to_tests, test_list


    def remove_commented(self, file_contents):
        contents = []
        for line_tup in file_contents:
            line = line_tup[1]
            if len(line.lstrip()) > 0:
                if line.lstrip()[0] != "#":
                    contents.append((line_tup[0], line.lstrip()))
        return contents


    def split_lines(self, file_contents):
        contents = []
        for line_tup in file_contents:
            line = line_tup[1]
            line_num = line_tup[0]
            line = line.split('=')
            if len(line) < 2:
                raise SyntaxError(message="Not enough '='.", line_num=line_num)
            elif len(line) > 2:
                raise SyntaxError(message="Too many '='.", line_num=line_num)

            line = [l.split() for l in line]
            if len(line[0]) == 0:
                raise SyntaxError(message="Nothing before '='.", line_num=line_num)
            elif len(line[0]) > 1:
                raise SyntaxError(message="Too many space separated items before '='.", line_num=line_num)

            if len(line[1]) == 0:
                raise SyntaxError(message="Nothing after '='.", line_num=line_num)
            elif len(line[1]) > 2:
                raise SyntaxError(message="Too many space separated items after '='.", line_num=line_num)

            line_dic = {"var": line[0][0], "vals": line[1]}
            contents.append((line_num, line_dic))
        return contents


    def parse_vars(self, file_contents):
        test_list = []
        path_to_tests = None
        for line_tup in file_contents:
            line_num = line_tup[0]
            var = line_tup[1]["var"]
            vals = line_tup[1]["vals"]

            if var.lower() == "path_to_tests":
                if len(vals) == 0:
                    raise SyntaxError(message="No path to tests.", line_num=line_num)
                elif len(vals) > 1:
                    raise SyntaxError(message="Too many paths to tests.", line_num=line_num)
                path_to_tests = vals[0]
            elif var.lower() == "test":
                if len(vals) < 2:
                    raise SyntaxError(message="Need both program name and test name.", line_num=line_num)
                elif len(vals) > 2:
                    raise SyntaxError(message="Too many values after test. Only need program name and test name.", line_num=line_num)
                test_list.append({"program": vals[0], "test": vals[1]})
            else:
                raise SyntaxError(message="Incorrect variable to set. Should be either 'path_to_tests' or 'test'.", line_num=line_num)

        if path_to_tests == None:
            raise Exception("No path to tests found.")
        return path_to_tests, test_list


class SyntaxError(Exception):
    def __init__(self, message, line_num=-1):
        super().__init__(message)
        self.message = message
        self.line_num = line_num

    def toString(self, unchanged_contents):
        new_message = self.message
        if self.line_num != -1:
            new_message += "\nline " + str(self.line_num) + ":\t" + unchanged_contents[self.line_num]
        return new_message


if __name__ == '__main__':
    rgtin_path = "/Users/cameronkuchta/Documents/GitHub/harmony/sample_inputs/rgt.input.master"
    job_id_path = "/Users/cameronkuchta/Documents/GitHub/harmony/sample_inputs/sample_run/GTC4/test_0001node/Status/123456789.0123/job_id.txt"
    parseID = ParseJobID()
    print(parseID.parse_file(job_id_path))
