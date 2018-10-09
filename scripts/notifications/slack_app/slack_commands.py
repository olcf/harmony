# Commands needed:
#   help
#   my jobs
#   check tests
from scripts import job_monitor
import functools


class docstring_parameter:
    def __init__(self, **kwargs):
        self.kws = kwargs

    def __call__(self, obj):
        obj.__doc__ = obj.__doc__.format(**self.kws)
        return obj


class is_command:
    def __init__(self, command=True):
        self.command = command

    def __call__(self, obj):
        obj.is_command = self.command
        return obj


def get_functions(cls):
    functions = {}
    for key in sorted(cls.__dict__.keys()):
        if callable(cls.__dict__[key]) and '__' not in key:
            func = cls.__dict__[key]
            if hasattr(func, 'is_command'):
                if func.is_command:
                    functions[key] = cls.__dict__[key]

    return functions


def make_columns(tuple_list, col_sizes=[10, 20, 20]):
    string = ""
    if len(tuple_list) == 0:
        return string
    if len(tuple_list[0]) != len(col_sizes):
        raise ValueError("Invalid column sizes. Cannot understand " + str(len(col_sizes)) +
                         " defining " + str(len(tuple_list[0])) + " columns.")

    tuple_list = [tuple([str(val) for val in tup]) for tup in tuple_list]

    col_sizes = maximize_col_sizes(tuple_list, col_sizes)

    for i in range(len(tuple_list)):
        tup = tuple_list[i]

        unformatted = ""
        for j in range(len(tup)):
            unformatted += "{" + str(j) + ":<" + str(col_sizes[j]) + "} "

        # Unpack the tuple with '*' operator and format it.
        string += unformatted.format(*tup)
        if i < len(tuple_list) - 1:
            string += "\n"

    return string


def maximize_col_sizes(tuple_list, col_sizes):
    new_cols = [0] * len(col_sizes)
    for i in range(len(col_sizes)):
        max_col_size = max((len(tup[i]) for tup in tuple_list))
        new_cols[i] = max(max_col_size, col_sizes[i])
    return new_cols


class MessageParser():
    bot_name = 'Botty McBotterson'

    def __init__(self, watch_time=600):
        parser_functions = get_functions(MessageParser)

        try:
            from pythonlsf import lsf
        except ModuleNotFoundError:
            self.on_summit = False
        else:
            self.on_summit = True

        # Create dictionary of commands.
        self.command_descriptions = ""
        for key in sorted(parser_functions):
            if hasattr(parser_functions[key], 'is_command'):
                if parser_functions[key].is_command:
                    self.command_descriptions += "*" + key + "*:\t" + parser_functions[key].__doc__ + "\n\n"

        self.watch_time = watch_time

        self.JM = job_monitor.JobMonitor()

        self.path_to_previous_rgt = None

    def parse_message(self, entire_message, slack_sender, channel):
        message = str(entire_message['text'])
        slack_user = str(entire_message['user'])

        if 'help' in message:
            return self.slack_help()

        elif 'my_jobs' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            message = message.split()
            index = message.index('my_jobs')
            try:
                username = message[index + 1]
            except IndexError:
                return "I can't find your username."
            return self.my_jobs(username)

        elif 'all_jobs' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            return self.all_jobs()

        elif 'check_tests' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            message = message.split()
            index = message.index('check_tests')
            try:
                path = message[index + 1]
            except IndexError:
                path = None

            return self.check_tests(path_to_rgt=path)

        elif 'monitor_job' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            message = message.split()
            index = message.index('monitor_job')
            str_ids = message[(index + 1):]

            job_ids = []
            for str_id in str_ids:
                try:
                    job_ids.append(int(str_id))
                except ValueError:
                    return "I don't understand the a job id that looks like '" + str_id + "'."

            if len(job_ids) == 0:
                return "I can't find the job id that you wanted to monitor in the message you sent me. \n" + \
                       "The job may exist, I just can't get the id out of your message."
            return self.monitor_job(job_ids, slack_sender, channel, slack_user)

        else:
            return "I don't understand what exactly you wanted me to do with '" + message + "'. " + self.slack_help()

    @is_command()
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
        from scripts.job_status import JobStatus
        JS = JobStatus()
        jobs = JS.get_jobs_by_user(username)
        if len(jobs) == 1:
            response = "I found 1 job by " + username + ".\n"
        else:
            response = "I found " + str(len(jobs)) + " jobs by " + username + ".\n"

        tuple_list = [(job.jobId, job.jobName, job.status) for job in jobs]
        tuple_list.insert(0, ("JOBID", "JOBNAME", "STATUS"))
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
        returner = lambda x: x

        message = ""
        if path_to_rgt is None:
            if self.path_to_previous_rgt is None:
                return "I'm not sure what rgt input you would like me to test."
            else:
                message += "I am assuming you want me to recheck " + self.path_to_previous_rgt + ".\n"
        elif path_to_rgt is not None:
            self.path_to_previous_rgt = path_to_rgt

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

        self.JM.refresh_threads()
        if len(self.JM.running_monitors) + 1 > self.JM.max_monitors:
            return "<@" + slack_user + "> I can't watch this job yet. " \
                   "I'm already watching " + self.JM.max_monitors + " jobs!"
        self.JM.monitor_jobs(job_ids=jobID, watch_time=self.watch_time, notifier=send, user=slack_user)
        return "I have started monitoring " + str(jobID) + "."

    @is_command()
    @docstring_parameter(bot=bot_name)
    def all_jobs(self):
        """
        Show all jobs currently on LSF.

        :return: All jobs.
        """
        from scripts.job_status import JobStatus
        JS = JobStatus()
        jobs = JS.get_jobs()

        if len(jobs) == 1:
            response = "I found 1 job in LSF.\n"
        else:
            response = "I found " + str(len(jobs)) + " jobs in LSF.\n"

        tuple_list = [(job.jobId, job.user, job.jobName, job.status) for job in jobs]
        tuple_list.insert(0, ("JOBID", "USER", "JOBNAME", "STATUS"))
        response += "```" + make_columns(tuple_list) + "```"

        return response
