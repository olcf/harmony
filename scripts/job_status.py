""" Find the status of some set of jobs."""

from pythonlsf import lsf
from scripts import connect
import sys
from collections import Counter


class JobStatus:
    """
    Get the status of a set of jobs in LSF according to some property they share.
    """

    def __init__(self, queue='batch', verbose=False):
        """
        Connect to lsf and set the verbosity.
        """
        connect.connect(queue)
        self.verbose = verbose

    def in_queue(self, jobID):
        """
        Test if a certain jobID is in the queue/running.

        :param jobID: (int) ID of job to test status of.
        :return: (boolean) Whether the job is in queue.
        """
        # Get all the jobs that match that jobID and are either eligible, current, or blocked.
        queue_stats = ['eligible', 'running', 'blocked']
        queue_stats = [Job.possible_status[stat] for stat in queue_stats]
        jobs = self.get_jobs(jobid=jobID, status=queue_stats)
        # If that job exists then all good.
        if len(jobs) != 0:
            return True
        else:
            return False

    def get_jobs_by_user(self, user):
        """
        Find the set of jobs in LSF by username.

        :param user: (str) Name of user who's jobs will be found.
        :return: (list) List of jobs from that user.
        """
        return self.get_jobs(user=user)

    def get_jobs_by_jobid(self, jobid):
        """
        Get all jobs by their jobID. This should only ever return at most one job.

        :param jobid: (int) jobID to get corresponding job.
        :return: (list) List containing all jobs with that id.
        """
        return self.get_jobs(jobid=jobid)

    def get_jobs_by_name(self, jobName):
        """
        Find a job according to it's name. There may be multiple jobs with the same name.

        :param jobName: (str) Name of job to find.
        :return: (list) List of jobs found with that name.
        """
        return self.get_jobs(jobName=jobName)

    def get_jobs_by_status(self, status):
        """
        Get all jobs with a certain status or list of statuses.

        :param status: (str, list) A string containing a single status to find or a list that looks for any matches of any status
               in that string.
        :return: (list) List of jobs that have that set of statuses.
        """
        return self.get_jobs(status=status)

    def count_type(self, jobs):
        """
        Input a set of jobs and count how many are of each status type.

        :param jobs: (list) A set of jobs.
        :return: (Counter) Object that has occurence of each status.
        """
        stats = []
        for j in jobs:
            stats.append(j.status)
        cnt = Counter(stats)
        return cnt

    def get_job_status(self, jobid):
        """
        Send in the id of some job and get it's corresponding status.

        :param jobid: (int) Id of job whose status will be found.
        :return: (str) Status of job.
        """
        # Get the job.
        jobs = self.get_jobs(jobid=jobid)
        # If no job with this id exists then error.
        if len(jobs) == 0:
            if self.verbose:
                print("There is no job with ID " + str(jobid))
            return None
        # If multiple jobs with this id exist then error.
        elif len(jobs) > 1:
            raise KeyError("Too many jobs with ID", jobid)
        # Return the status of the job.
        return jobs[0].status

    def get_job_exit_status(self, jobid):
        """
        Send in the id of some job and get it's corresponding exit status if it has one.

        :param jobid: Id of job whose exit status will be found.
        :return: The exit status of the job.
        """
        # Get the job.
        jobs = self.get_jobs(jobid=jobid)
        # If no job with that id exists, then error.
        if len(jobs) == 0:
            if self.verbose:
                print("There is no job with ID " + str(jobid))
            return None
        elif len(jobs) > 1:
            raise KeyError("There are too many jobs with ID", jobid)
        # Return the exit status of the job.
        return jobs[0].exit_status

    def get_jobs(self, jobid=0, jobName=None, user="all", queue=None, hostname=None, status='all'):
        """
        Enter certain parameters to reduce the search space of all jobs in LSF or that have been recently completed.
        The default is to return all possible jobs.

        :param  jobid: (int) jobid to match with.
        :param  jobName: (str) Name of job to match.
        :param  user: (str) User to match.
        :param  queue: (str) LSF queue to search.
        :param  hostname: (str) Hostname to search.
        :param  status: (str, list) Group of status to match.
        :return: (list) List of jobs that match above criteria.
        """
        # Since attempting to choose job status based on options does not work, we instead filter the jobs after
        # we have found all the matches.
        search_status = lsf.ALL_JOB
        if status == "all":
            status = Job.get_viable_status()
        job_status = Job.get_viable_status()

        # LSF uses numbers for each type of job so initialize the options as 0.
        options = []
        # Try to go through all status' set.
        try:
            # If the user entered a list, the options are already set. Just make sure they are all in the dictionary.
            if type(status) is list:
                # Using or, put that status into the possible job options.
                for s in status:
                    if s not in job_status:
                        raise KeyError
                    options.append(s)
            # If it is a string then it is only one status to look for.
            elif type(status) is str:
                if status not in job_status:
                    raise KeyError
                options.append(status)
        # If incorrect key was entered then print out error with correct options.
        except KeyError:
            status_str = ""
            index = 0
            for key in job_status:
                status_str += key 
                status_str += ", "
                index += 1
            status_str += "all"
            raise KeyError("Invalid status, " + str(status) + ". Options are: " + status_str)

        # Create an array for holding each job.
        jobs = []
        if self.verbose:
            print("jobid:", jobid, "jobName:", jobName, "user:", user, "queue:", queue, "hostname:", hostname, "options:", search_status)
        # Get a generator that will return a job whenever querried.
        jobinfohead = lsf.lsb_openjobinfo_a(jobid, jobName, user, queue, hostname, search_status)

        # If there are some jobs that exist under certain parameters then get the number of jobs.
        if jobinfohead is not None:
            num_jobs = jobinfohead.numJobs
        # Otherwise there are no jobs.
        else:
            num_jobs = 0

        if self.verbose:
            print("Found " + str(num_jobs) + " job(s)")

        # Repeatedly call jobinfo for how many jobs are there.
        for _ in range(num_jobs):
            # Append the job to the list after transforming it into a Job class.
            # Once job info is closed, lsf.lsb_readjobinfo does not work again.
            # It is also a generator and can thus only be gone through once.
            lsf_job = lsf.lsb_readjobinfo(None) 
            # This occurs if the job pops out of queue after getting the number of lsf jobs.
            if lsf_job is None:
                continue
            j = Job(lsf_job)
            if j.status in options:
                jobs.append(j)
        # All done with this job info.
        lsf.lsb_closejobinfo()

        # Return the list of jobs.
        return jobs


class Job:
    """
    Hold the information of some job. This is useful since the job info from lsf.<job info> is only temporary.
    """

    # Hold all possible status for any job.
    possible_status = {'running':'Running',
                       'complete':'Complete',
                       'walltimed': 'Walltimed',
                       'killed': 'Killed',
                       'susp_person_dispatched': 'Susp_person_dispatched',
                       'susp_person_pend': 'Susp_person_pend',
                       'susp_system': 'Susp_system',
                       'eligible': 'Eligible',
                       'blocked': 'Blocked',
                       'unknown': 'Unknown'}

    @staticmethod
    def get_viable_status():
        """
        Get all possible status for a job.
        """
        stats = []
        for key in Job.possible_status.keys():
            stats.append(Job.possible_status[key])
        return stats

    def __init__(self, j):
        """
        Initialize the job with its id, total allowed run time., and status.

        :param j: (lsf job) The object that comes from the pythonlsf generator.
        """
        # Record jobID.
        self.jobId = j.jobId
        # Record job name.
        self.jobName = j.jName
        # Record user who submitted job.
        self.user = j.user
        # Set the exit status value initially to None. If it has one, it is changed later on.
        self.exit_status = int(j.exitStatus)

        # Get the status of the job.
        if j.status & lsf.JOB_STAT_RUN:
            self.status = self.possible_status["running"]
        elif j.status & lsf.JOB_STAT_DONE:
            self.exit_status = int(j.exitStatus)
            self.status = self.possible_status["complete"]
        elif j.status & lsf.JOB_STAT_EXIT:
            self.exit_status = int(j.exitStatus)
            # I think that error code 140 always means runlimit exceeded and there is no other code.
            # I'm not totally sure about that though.
            if (int(j.exitStatus) % 256) == 140:
                self.status = self.possible_status["walltimed"]
            else:
                self.status = self.possible_status["killed"]
        elif j.status & lsf.JOB_STAT_USUSP:
            self.status = self.possible_status["susp_person_dispatched"]
        elif j.status & lsf.JOB_STAT_PSUSP:
            self.status = self.possible_status["susp_person_pend"]
        elif j.status & lsf.JOB_STAT_SSUSP:
            self.status = self.possible_status["susp_system"]
        elif j.status & lsf.JOB_STAT_PEND:
            if j.pendStateJ == 0:
                self.status = self.possible_status["eligible"]
            else:
                self.status = self.possible_status["blocked"]
        else:
            self.status = self.possible_status["unknown"]


if __name__ == "__main__":
    # If the this was called with some param, assume it is the jobID.
    if len(sys.argv) > 1:
        jobid = int(sys.argv[1])
    else:
        jobid = 0
    # Create the job querying class.
    js = JobStatus(queue='batch')
    # Get the jobs. If jobid is 0 then it will get all jobs.
    jobs = js.get_jobs(jobid=jobid)
    # For each job, print it's information.
    for j in jobs:
        stat = j.status
        jobid = j.jobId
        print(jobid, '\t', stat)

