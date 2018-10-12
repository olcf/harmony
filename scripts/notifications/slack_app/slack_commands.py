# Commands needed:
#   help
#   my jobs
#   check tests
from scripts import job_monitor
import os


class docstring_parameter:
    """
    Hold parameters for the docstring of some method.
    """
    def __init__(self, **kwargs):
        self.kws = kwargs

    def __call__(self, obj):
        obj.__doc__ = obj.__doc__.format(**self.kws)
        return obj


class is_command:
    """
    Hold whether the function this is a decorator for is a slack command.
    """
    def __init__(self, command=True):
        self.command = command

    def __call__(self, obj):
        obj.is_command = self.command
        return obj


def get_functions(cls):
    """
    Get all slack commands in a class.

    :param cls: Class to find functions from.
    :return: Dictionary of functions containing name and function.
    """
    functions = {}
    for key in sorted(cls.__dict__.keys()):
        if callable(cls.__dict__[key]) and '__' not in key:
            func = cls.__dict__[key]
            if hasattr(func, 'is_command'):
                if func.is_command:
                    functions[key] = cls.__dict__[key]

    return functions


def make_columns(tuple_list, col_sizes=[10, 20, 20]):
    """
    Make formatted columns from a list of tuples. Column size is enlarged if the input columns are
    too small to correctly format the data.

    :param tuple_list: A list of tuples to turn into columns.
    :param col_sizes: Size of columns to make.
    :return: Formatted columns.
    """

    # Initialize an empty sting.
    string = ""
    # Make sure the list is not empty.
    if len(tuple_list) == 0:
        return string
    # Check that there are the correct number of columns to values.
    if len(tuple_list[0]) != len(col_sizes):
        raise ValueError("Invalid column sizes. Cannot understand " + str(len(col_sizes)) +
                         " defining " + str(len(tuple_list[0])) + " columns.")

    # Change list of tuples into list of tuples only containing strings.
    tuple_list = [tuple([str(val) for val in tup]) for tup in tuple_list]

    # Get new column sizes for columns that were not wide enough when set.
    col_sizes = maximize_col_sizes(tuple_list, col_sizes)

    # For each tuple, format it and put it into the string.
    for i in range(len(tuple_list)):
        tup = tuple_list[i]

        # Create the unformatted string containing which value and column width.
        unformatted = ""
        for j in range(len(tup)):
            unformatted += "{" + str(j) + ":<" + str(col_sizes[j]) + "} "

        # Unpack the tuple with '*' operator and format it.
        string += unformatted.format(*tup)
        # If there will be another line, add an end line.
        if i < len(tuple_list) - 1:
            string += "\n"

    # Return the fully formatted string.
    return string


def maximize_col_sizes(tuple_list, col_sizes):
    """
    Take a list of tuples containing strings and column widths and make sure each string can fit in the column width.
    If not then enlarge the column.

    :param tuple_list: List of tuples containing strings.
    :param col_sizes: List of sizes for each column.
    :return: The correctly sized columns.
    """

    # Create list to hold new columns.
    new_cols = [0] * len(col_sizes)
    # Iterate over columns.
    for i in range(len(col_sizes)):
        # Get the maximum sized element in that column in the list of tuples.
        max_col_size = max((len(tup[i]) for tup in tuple_list))
        # Get the larger of the two, whether that be the input column size or the max elements size.
        new_cols[i] = max(max_col_size, col_sizes[i])
    # Return the new column sizes.
    return new_cols


class MessageParser():
    """
    Class to hold the parser for messages.
    """

    # Get the name of the bot from the environment. This is needed so that the documentation on methods is nice
    # when printed to slack.
    bot_name = os.environ["SLACK_BOT_NAME"]

    def __init__(self, watch_time=600):
        # Get all the slack functions in this class.
        parser_functions = get_functions(MessageParser)

        # Try to import lsf. If it works then we are on summit.
        try:
            from pythonlsf import lsf
        except ModuleNotFoundError:
            self.on_summit = False
        else:
            self.on_summit = True

        # Create string for holding descriptions of commants.
        self.command_descriptions = ""
        # For each function, add it's name and documentation to the output.
        for key in sorted(parser_functions):
            if hasattr(parser_functions[key], 'is_command'):
                if parser_functions[key].is_command:
                    self.command_descriptions += "*" + key + "*:\t" + parser_functions[key].__doc__ + "\n\n"

        # Set how often watching activates.
        self.watch_time = watch_time

        # Set up a job monitor for later use.
        self.JM = job_monitor.JobMonitor()

        # Initialize the previous path as nothing.
        self.path_to_previous_rgt = None

    def parse_message(self, entire_message, slack_sender, channel):
        """
        Take in a message from slack and parse the important info from it and run the correct command.

        :param entire_message: The response dictionary from the server.
        :param slack_sender: How to send the response message if using a job monitor. Otherwise it is just a return val.
        :param channel: Where to send to.
        :return: The response we make.
        """

        # Get the text of the message and user.
        message = str(entire_message['text'])
        slack_user = str(entire_message['user'])

        # Test if the user is asking for the commands.
        if 'help' in message:
            return self.slack_help()
        # Test if the user wants to see some users jobs.
        elif 'my_jobs' in message:
            # Check if on summit.
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            # Split the message.
            message = message.split()
            # Get the index of where 'my_jobs' is. The username should be immediately after this.
            index = message.index('my_jobs')
            # Try to get the username. If there is no text after it then inform the user that the username is not found.
            try:
                username = message[index + 1]
            except IndexError:
                return "I can't find your username."
            # Return the response to searching for that username.
            return self.my_jobs(username)
        # Test if the user wants to see all jobs currently running.
        elif 'all_jobs' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            return self.all_jobs()
        # Check if all tests in some path are running.
        elif 'check_tests' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            # Split the message and get the path to where their rgt input is.
            message = message.split()
            index = message.index('check_tests')
            try:
                path = message[index + 1]
            except IndexError:
                path = None

            return self.check_tests(path_to_rgt=path)
        # Test if a user wants to monitor a job.
        elif 'monitor_job' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            # Get all job ids in the message.
            message = message.split()
            index = message.index('monitor_job')
            str_ids = message[(index + 1):]

            # Try to get the actual ids. If it fails to be an int then return a message.
            job_ids = []
            for str_id in str_ids:
                try:
                    job_ids.append(int(str_id))
                except ValueError:
                    return "I don't understand the a job id that looks like '" + str_id + "'."

            # If no job ids found in message, inform user.
            if len(job_ids) == 0:
                return "I can't find the job id that you wanted to monitor in the message you sent me. \n" + \
                       "The job may exist, I just can't get the id out of your message."
            return self.monitor_job(job_ids, slack_sender, channel, slack_user)
        # If we could not understand the message, tell the user.
        else:
            return "I don't understand what exactly you wanted me to do with '" + message + "'. " + self.slack_help()

    # Decorate function so it is labeled as a slack command.
    @is_command()
    # Add a parameter to the docstring.
    @docstring_parameter(bot=bot_name)
    def slack_help(self):
        """
        Show all commands that I can run.

        USAGE: @{bot} help
        :return: This message.
        """
        response = "Here is what I can do! \n\n" + self.command_descriptions
        return response

    @is_command()
    @docstring_parameter(bot=bot_name)
    def my_jobs(self, username):
        """
        Show all jobs currently running by some user.

        USAGE: @{bot} my_jobs <username>
        :param username: Some username.
        :return: All jobs running by <username>.
        """

        # Import JobStatus so that we can search lsf.
        from scripts.job_status import JobStatus
        JS = JobStatus()
        jobs = JS.get_jobs_by_user(username)
        # Set up the start of the response.
        if len(jobs) == 1:
            response = "I found 1 job by " + username + ".\n"
        else:
            response = "I found " + str(len(jobs)) + " jobs by " + username + ".\n"

        # Create a list of jobs and add headers.
        tuple_list = [(job.jobId, job.jobName, job.status) for job in jobs]
        tuple_list.insert(0, ("JOBID", "JOBNAME", "STATUS"))
        # Make columns and add '```' so that it is correctly formatted.
        response += "```" + make_columns(tuple_list) + "```"

        return response

    @is_command()
    @docstring_parameter(bot=bot_name)
    def check_tests(self, path_to_rgt=None):
        """
        Check all harmony tests. A path does not need to be entered.
        If there is no path, the previous path checked will be used.

        USAGE: @{bot} check_tests <path>
        :param path_to_rgt: The path to the rgt_input file that can be accessed by everyone.
        :return: All tests currently running.
        """

        # Set it to notify by returning the value.
        returner = lambda x: x

        # Initialize the message.
        message = ""
        # If no path exists in message, check if there was a previous path and if so add it to the message.
        if path_to_rgt is None:
            if self.path_to_previous_rgt is None:
                return "I'm not sure what rgt input you would like me to test."
            else:
                message += "I am assuming you want me to recheck " + self.path_to_previous_rgt + ".\n"
        # If path is in message, use it.
        elif path_to_rgt is not None:
            self.path_to_previous_rgt = path_to_rgt

        # Check the tests in that path.
        from scripts import test_status
        return test_status.check_tests(path_to_rgt, notifier=returner)

    @is_command()
    @docstring_parameter(bot=bot_name)
    def monitor_job(self, jobID, slack_sender, channel, slack_user):
        """
        Continue checking on a job and notify when it changes status.

        USAGE: @{bot} monitor_job <jobID> [<jobID>, ...]
        :param jobID: The ID of the job to check.
        :return: An update whenever the job does something in LSF.
        """
        # We need to create a monitor.
        # Then we pass it in a function that it can call to send out a notification of some sort.
        def send(user=None, job_id=None, status=None, new_status=None, done=False, error_message=None):
            message = "<@" + user + "> [" + str(job_id) + "] "
            if error_message is not None:
                message += error_message
            elif new_status is None:
                if not done:
                    message += "The job is currently " + status + "."
                else:
                    message += "The job is done with state " + status + "."
            else:
                message += "The job has changed from " + status + " to " + new_status + "!"

            slack_sender.send_message(channel, message)

        # Remove any dead monitors.
        self.JM.refresh_threads()
        # If there are too many monitors, don't try to monitor anothr.
        if len(self.JM.running_monitors) + 1 > self.JM.max_monitors:
            return "<@" + slack_user + "> I can't watch this job yet. " \
                   "I'm already watching " + self.JM.max_monitors + " jobs!"
        # Start a monitor.
        self.JM.monitor_jobs(job_ids=jobID, watch_time=self.watch_time, notifier=send, user=slack_user)
        # Inform the user that the message has been recieved.
        return "I have started monitoring " + str(jobID) + "."

    @is_command()
    @docstring_parameter(bot=bot_name)
    def all_jobs(self):
        """
        Show all jobs currently on LSF.

        :return: All jobs.
        """

        # Get all jobs from lsf.
        from scripts.job_status import JobStatus
        JS = JobStatus()
        jobs = JS.get_jobs()

        # Set up the beginning of the response.
        if len(jobs) == 1:
            response = "I found 1 job in LSF.\n"
        else:
            response = "I found " + str(len(jobs)) + " jobs in LSF.\n"

        # Create a list of jobs.
        tuple_list = [(job.jobId, job.user, job.jobName, job.status) for job in jobs]
        # Add headers to message.
        tuple_list.insert(0, ("JOBID", "USER", "JOBNAME", "STATUS"))
        # Format the message and send it back.
        response += "```" + make_columns(tuple_list) + "```"

        return response
