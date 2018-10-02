# Commands needed:
#   help
#   my jobs
#   check tests


def docstring_parameter(*args, **kwargs):
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*args, **kwargs)
        return obj
    return dec

def get_functions(cls):
    functions = {}
    for key in sorted(cls.__dict__.keys()):
        if callable(cls.__dict__[key]) and '__' not in key:
            functions[key] = cls.__dict__[key]

    return functions

def make_columns(tuple_list, col_sizes=[8, 15, 15]):
    string = ""
    if len(tuple_list) == 0:
        return string
    if len(tuple_list[0]) != len(col_sizes):
        raise ValueError("Invalid column sizes. Cannot understand " + len(col_sizes) +
                         " defining " + len(tuple_list[0]) + " columns.")

    for tuple in tuple_list:
        unformatted = ""
        for i in range(len(tuple)):
            if i == 0:
                unformatted += "{" + i + ":<" + col_sizes[i] + "} "
            else:
                unformatted += "{" + i + ":>" + col_sizes[i] + "} "

        string += unformatted.format(tuple) + "\n"

    return string

class MessageParser():
    bot_name = 'Botty McBotterson'

    def __init__(self, watch_time):
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
                self.command_descriptions += key + ":\t" + parser_functions[key].__doc__ + "\n\n"

        self.watch_time = watch_time

    def parse_message(self, message):
        if 'help' in message:
            return self.slack_help()

        elif 'my_jobs' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            message = message.split()
            index = message.index('my_jobs')
            username = message[index + 1]
            return self.my_jobs(username)

        elif 'all_jobs' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."
            return self.all_jobs()

        elif 'check_tests' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."

        elif 'monitor_job' in message:
            if not self.on_summit:
                return "I can't seem to find LSF so '" + message + "' won't work."

        else:
            return "I don't understand what exactly you wanted me to do with '" + message + "'. " + self.slack_help()

    @docstring_parameter(bot=bot_name)
    def slack_help(self):
        """
        Show all commands that I can run.

        USAGE: @{bot} help
        :return: This message.
        """
        response = "Here is what I can do! \n\n" + self.command_descriptions
        return response
    slack_help.is_command = True

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
            response = "I found " + len(jobs) + " jobs by " + username + ".\n"

        tuple_list = [(job.jobId, job.jobName, job.status) for job in jobs]
        response += make_columns(tuple_list)

        return response
    my_jobs.is_command = True

    @docstring_parameter(bot=bot_name)
    def check_tests(self, path_to_rgt=None):
        """
        Check all harmony tests.

        USAGE: @{bot} check_tests <path>
        :param path_to_rgt: The path to the rgt_input file that can be accessed by everyone.
        :return: All tests currently running.
        """
        returner = lambda x: x

        from scripts import test_status
        return test_status.check_tests(path_to_rgt, notifier=returner)
    check_tests.is_command = True

    @docstring_parameter(bot=bot_name)
    def monitor_job(self, jobID):
        """
        Continue checking on a job and notify when it changes status.
        NOT YET IMPLEMENTED

        :param jobID: The ID of the job to check.
        :return: An update whenever the job does something in LSF.
        """
        return
    monitor_job.is_command = True

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
            response = "I found " + len(jobs) + " jobs in LSF.\n"

        tuple_list = [(job.jobId, job.jobName, job.status) for job in jobs]
        response += make_columns(tuple_list)

        return response
    all_jobs.is_command = True

if __name__ == '__main__':
    MP = MessageParser()
    print(MP.parse_message(""))
