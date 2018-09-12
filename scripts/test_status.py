
def parse_file(file_path):
    # need path to tests
    # list of tests and application
    file_contents = []
    with open(file_path) as file:
        for line in file:
            stripped = line.lstrip()
            if len(stripped) > 0:
                if line.lstrip()[0] == "#":
                    continue
            else:
                continue
            file_contents.append(line)

    print(file_contents)


if __name__ == '__main__':
    file_path = "/Users/cameronkuchta/Documents/GitHub/harmony/sample_inputs/rgt.input.master"
    parse_file(file_path)
