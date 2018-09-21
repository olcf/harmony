""" Find the status of some set of jobs."""

from pythonlsf import lsf
from scripts import connect
import sys
from collections import Counter


# Create a class for doing all connections to LSF and asking for jobs.
class JobStatus:
    # Initialize the connection.
    def __init__(self, queue='batch', verbose=False):
        connect.connect(queue)
        self.verbose = verbose

    # Find the set of jobs in LSF by username.
    def get_jobs_by_user(self, user):
        return self.get_jobs(user=user)

    # Get all jobs by their jobID. This should only ever return at most one job.
    def get_jobs_by_jobid(self, jobid):
        return self.get_jobs(jobid=jobid)

    # Find a job according to it's name.
    def get_jobs_by_name(self, jobName):
        return self.get_jobs(jobName=jobName)

    # Get all jobs with a certain status or list of statuses.
    def get_jobs_by_status(self, status):
        return self.get_jobs(status=status)

    # Input a set of jobs and count how many are of each status type.
    def count_type(self, jobs):
        stats = []
        for j in jobs:
            stats.append(j.status)
        cnt = Counter(stats)
        return cnt

    # Send in the id of some job and get it's corresponding status.
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

    # Enter certain parameters to reduce the search space of all jobs in LSF or that have been recently completed.
    # The default is to return all possible jobs.
    def get_jobs(self, jobid=0, jobName=None, user="all", queue=None, hostname=None, status='all'):
        job_status = {'all': lsf.ALL_JOB, 'done': lsf.DONE_JOB, 'pending': lsf.PEND_JOB,
                      'suspended': lsf.SUSP_JOB, 'running': lsf.RUN_JOB, 'current': lsf.CUR_JOB,
                      'eligible': lsf.APS_JOB, 'exited': lsf.EXIT_JOB}

        # LSF uses numbers for each type of job so initialize the options as 0.
        options = 0
        # Try to go through all status' set.
        try:
            # If the user entered a list, go through each status in the list.
            if type(status) is list:
                # Using or, put that status into the possible job options.
                for s in status:
                    options |= job_status[s]
            # If it is a string then it is only one status to look for.
            elif type(status) is str:
                options = job_status[status]
        # If incorrect key was entered then print out error with correct options.
        except KeyError:
            status_str = ""
            for key in job_status.keys():
                status_str += key + " "
            raise KeyError("Invalid status. Options are " + status_str)

        # Create an array for holding each job.
        jobs = []
        if self.verbose:
            print("jobid:", jobid, "jobName:", jobName, "user:", user, "queue:", queue, "hostname:", hostname, "options:", options)
        # Get a generator that will return a job whenever querried.
        jobinfohead = lsf.lsb_openjobinfo_a(jobid, jobName, user, queue, hostname, options)

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
            jobs.append(Job(lsf.lsb_readjobinfo(None)))
        # All done with this job info.
        lsf.lsb_closejobinfo()

        # Return the list of jobs.
        return jobs


# Hold the information of some job. This is useful since the job info from lsf.<job info> is only temporary.
class Job:
    possible_status = {'running':'Running',
                       'complete':'Complete',
                       'walltimed': 'Walltimed',
                       'killed': 'Killed',
                       'susp_person': 'Susp_person',
                       'susp_system': 'Susp_system',
                       'eligible': 'Eligible',
                       'blocked': 'Blocked',
                       'unknown': 'Unknown'}

    @staticmethod
    def get_viable_status():
        stats = []
        for key in Job.possible_status.keys():
            stats.append(Job.possible_status[key])
        return stats

    # Initialize the job with its id, total allowed run time., and status.
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
            self.status = self.possible_status["susp_person"]
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

