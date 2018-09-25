""" Find the status of some set of jobs."""

from pythonlsf import lsf
from scripts import connect
import sys
from collections import Counter

class JobStatus:
    """
    Get the status of a set of jobs in LSF according to some property they share.
    """

    """
    Connect to lsf and set the verbosity.
    """
    def __init__(self, queue='batch', verbose=False):
        connect.connect(queue)
        self.verbose = verbose

    """
    Test if a certain jobID is in the queue/running.
    
    :argument (int) ID of job to test status of.
    :returns (boolean) Whether the job is in queue.
    """
    def in_queue(self, jobID):
        # Get all the jobs that match that jobID and are either eligible, current, or blocked.
        # Not sure if blocked is ok but whatever.
        jobs = self.get_jobs(jobid=jobID, status=['Eligible', 'Running', 'Blocked'])
        # If that job exists then all good.
        if len(jobs) != 0:
            return True
        else:
            return False

    """
    Find the set of jobs in LSF by username.
    
    :argument (str) Name of user who's jobs will be found.
    :returns (list) List of jobs from that user.
    """
    def get_jobs_by_user(self, user):
        return self.get_jobs(user=user)

    """
    Get all jobs by their jobID. This should only ever return at most one job.
    
    :argument (int) jobID to get corresponding job.
    :returns (list) List containing all jobs with that id.
    """
    def get_jobs_by_jobid(self, jobid):
        return self.get_jobs(jobid=jobid)

    """
    Find a job according to it's name. There may be multiple jobs with the same name.
    
    :argument (str) Name of job to find.
    :returns (list) List of jobs found with that name.
    """
    def get_jobs_by_name(self, jobName):
        return self.get_jobs(jobName=jobName)

    """
    Get all jobs with a certain status or list of statuses.
    
    :argument (str, list) A string containing a single status to find or a list that looks for any matches of any status
           in that string.
    :returns (list) List of jobs that have that set of statuses.
    """
    def get_jobs_by_status(self, status):
        return self.get_jobs(status=status)

    """
    Input a set of jobs and count how many are of each status type.
    
    :argument (list) A set of jobs.
    :returns (Counter) Object that has occurence of each status.
    """
    def count_type(self, jobs):
        stats = []
        for j in jobs:
            stats.append(j.status)
        cnt = Counter(stats)
        return cnt

    """
    Send in the id of some job and get it's corresponding status.
    
    :argument (int) Id of job whose status will be found.
    :returns (str) Status of job.
    """
    def get_job_status(self, jobid):
        # Get the job.
        jobs = self.get_jobs(jobid=jobid)
        # If no job with this id exists then error.
        if len(jobs) == 0:
            raise Exception("There is no job with ID", jobid)
        # If multiple jobs with this id exist then error.
        elif len(jobs) > 1:
            raise Exception("Too many jobs with ID", jobid)
        # Return the status of the job.
        return jobs[0].status

    """
    Enter certain parameters to reduce the search space of all jobs in LSF or that have been recently completed.
    The default is to return all possible jobs.
    
    :keyword (int) jobid: jobid to match with.
    :keyword (str) jobName: Name of job to match.
    :keyword (str) user: User to match.
    :keyword (str) queue: LSF queue to search.
    :keyword (str) hostname: Hostname to search.
    :keyword (str, list) status: Group of status to match.
    :returns (list) List of jobs that match above criteria.
    """
    def get_jobs(self, jobid=0, jobName=None, user="all", queue=None, hostname=None, status='all'):
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
            j = Job(lsf.lsb_readjobinfo(None))
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

    """
    Get all possible status for a job.
    """
    @staticmethod
    def get_viable_status():
        stats = []
        for key in Job.possible_status.keys():
            stats.append(Job.possible_status[key])
        return stats

    """
    Initialize the job with its id, total allowed run time., and status.
    
    :argument (lsf job) The object that comes from the pythonlsf generator.
    """
    def __init__(self, j):
        # Record jobID.
        self.jobId = j.jobId

        # Get the status of the job.
        # print("jobId:", self.jobId, "RUN:", lsf.JOB_STAT_RUN, "DONE:", lsf.JOB_STAT_DONE,"EXIT:", lsf.JOB_STAT_EXIT,
        #       "USUSP:", lsf.JOB_STAT_USUSP, "SSUSP:", lsf.JOB_STAT_SSUSP, "PEND:", lsf.JOB_STAT_PEND)
        if j.status & lsf.JOB_STAT_RUN:
            self.status = self.possible_status["running"]
        elif j.status & lsf.JOB_STAT_DONE:
            self.status = self.possible_status["complete"]
        elif j.status & lsf.JOB_STAT_EXIT:
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
    # If the this was called with some argument, assume it is the jobID.
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

