import os


def bjobs_to_file(bjobs_path):
    """
    Get the output of 'bjobs -u all -a' into a file.

    :param bjobs_path: (str) Path to location of bjobs command.
    """
    # Path to the command.
    bjobs_command = os.path.join(bjobs_path, 'bjobs_to_file.sh')
    # Path to the output file.
    bjobs_file = os.path.join(bjobs_path, 'example_bjobs.txt')

    import subprocess
    # Run the command.
    subprocess.check_call(["bash", bjobs_command, bjobs_file])


def parse_bjobs(file_path):
    """
    Parse the output of 'bjobs -u all -a' that is in a file.

    :param file_path: (str) Path to output of bjobs.
    :return: job_dics: (list) List of dictionaries containing necessary information of each job.
    """
    file_contents = []
    # Get file into list.
    with open(file_path) as f:
        for line in f:
            file_contents.append(line)

    # The first line is the line containing the variables in the bjobs output.
    variable_line = file_contents.pop(0)
    # Set the indices for where values are.
    jobid_index = [variable_line.find('JOBID'), variable_line.find('USER')]
    user_index = [variable_line.find('USER'), variable_line.find('STAT')]
    stat_index = [variable_line.find('STAT'), variable_line.find('SLOTS')]
    jobname_index = variable_line.find('JOB_NAME')

    job_dics = []
    # For each line, create a dictionary containing the necessary information.
    for line in file_contents:
        job_dics.append({'jobid': int(line[jobid_index[0]:jobid_index[1]].strip()),
                         'user': line[user_index[0]:user_index[1]].strip(),
                         'stat': line[stat_index[0]:stat_index[1]].strip(),
                         'jobname': line[jobname_index:].strip()})

    return job_dics

