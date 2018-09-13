""" Find the status of some set of jobs."""

from pythonlsf import lsf
from scripts import connect
import sys
from collections import Counter


class JobStatus:
    def init(self, queue='batch', verbose=False):
        connect.connect(queue)
        self.verbose = verbose

    def get_jobs_by_user(self, user):
        return self.get_jobs(user=user)

    def get_jobs_by_jobid(self, jobid):
        return self.get_jobs(jobid=jobid)

    def get_jobs_by_name(self, jobName):
        return self.get_jobs(jobName=jobName)

    def get_jobs_by_status(self, status):
        return self.get_jobs(status=status)

    def count_type(self, jobs):
        stats = []
        for j in jobs:
            stats.append(j.status)
        cnt = Counter(stats)
        return cnt

    def get_job_status(self, jobid):
        jobs = self.get_jobs(jobid=jobid)
        if len(jobs) == 0:
            raise Exception("There is no job with ID", jobid)
        elif len(jobs) > 1:
            raise Exception("Too many jobs with ID", jobid)
        return jobs[0].status

    def get_jobs(self, jobid=0, jobName=None, user="all", queue=None, hostname=None, status='all'):
        job_status = {'all': lsf.ALL_JOB, 'done': lsf.DONE_JOB, 'pending': lsf.PEND_JOB,
                      'suspended': lsf.SUSP_JOB, 'running': lsf.RUN_JOB, 'current': lsf.CUR_JOB,
                      'eligible': lsf.APS_JOB}
        options = 0
        try:
            if type(status) is list:
                for s in status:
                    options |= job_status[s]
            elif type(status) is str:
                options = job_status[status]
        except KeyError:
            status_str = ""
            for key in job_status.keys():
                status_str += key + " "
            raise KeyError("Invalid status. Options are " + status_str)

        jobs = []
        if self.verbose:
            print("jobid:", jobid, "jobName:", jobName, "user:", user, "queue:", queue, "hostname:", hostname, "options:", options)
        jobinfohead = lsf.lsb_openjobinfo_a(jobid, jobName, user, queue, hostname, options)

        if jobinfohead is not None:
            num_jobs = jobinfohead.numJobs
        else:
            num_jobs = 0

        if self.verbose:
            print("Found " + str(num_jobs) + " job(s)")

        for _ in range(num_jobs):
            jobs.append(Job(lsf.lsb_readjobinfo(None)))
        lsf.lsb_closejobinfo()

        return jobs


class Job:
    def __init__(self, j):
        # Record jobID
        self.jobId = j.jobId
        self.walltime = j.submit.rLimits[lsf.LSF_RLIMIT_RUN]

        # Get the status of the job.
        # print("jobId:", self.jobId, "RUN:", lsf.JOB_STAT_RUN, "DONE:", lsf.JOB_STAT_DONE,"EXIT:", lsf.JOB_STAT_EXIT, "USUSP:", lsf.JOB_STAT_USUSP, "SSUSP:", lsf.JOB_STAT_SSUSP, "PEND:", lsf.JOB_STAT_PEND)
        if j.status & lsf.JOB_STAT_RUN:
            self.status = "Running"
        elif j.status & lsf.JOB_STAT_DONE:
            self.status = "Complete"
        elif j.status & lsf.JOB_STAT_EXIT:
            if (j.startTime - j.endTime) >= self.walltime:
                self.status = "Walltimed"
            else:
                self.status = "Killed"
        elif j.status & lsf.JOB_STAT_USUSP:
            self.status = "Susp_person"
        elif j.status & lsf.JOB_STAT_SSUSP:
            self.status = "Susp_system"
        elif j.status & lsf.JOB_STAT_PEND:
            if j.pendStateJ == 0:
                self.status = "Eligible"
            else:
                self.status = "Blocked_system"
        elif j.status & lsf.JOB_STATE_PEND:
            self.status = "Blocked_person"
        else:
            self.status = "Unknown"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        jobid = int(sys.argv[1])
    else:
        jobid = 0
    js = JobStatus()
    js.init(queue='batch')
    jobs = js.get_jobs()
    for j in jobs:
        stat = j.status
        jobid = j.jobId
        print(jobid, '\t', stat)

