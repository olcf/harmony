""" Find the status of some set of jobs."""

from pythonlsf import lsf
import connect
import sys

def get_job_set(jobid=0, jobName=None, user=None, queue=None, hostname=None, options=(lsf.CUR_JOB|lsf.APS_JOB), verbose=False):
    jobs = []
    if verbose:
        print("jobid:", jobid, "jobName:", jobName, "user:", user, "queue:", queue, "hostname:", hostname, "options:", options)
    jobinfohead = lsf.lsb_openjobinfo_a(jobid, jobName, user, queue, hostname, options)

    if jobinfohead is not None:
        num_jobs = jobinfohead.numJobs
    else:
        num_jobs = 0

    if verbose:
        print("Found " + str(num_jobs) + " job(s)")

    for _ in range(num_jobs):
        jobs.append(Job(lsf.lsb_readjobinfo(None)))
    lsf.lsb_closejobinfo()

    return jobs


class Job(object):
    def __init__(self, j):
        # Record jobID
        self.jobId = j.jobId

        # Get the status of the job.
        if j.status:
            print("jobId:", self.jobId, "RUN:", lsf.JOB_STAT_RUN, "DONE:", lsf.JOB_STAT_DONE,"EXIT:", lsf.JOB_STAT_EXIT, "USUSP:", lsf.JOB_STAT_USUSP, "SSUSP:", lsf.JOB_STAT_SSUSP, "PEND:", lsf.JOB_STAT_PEND)
            if lsf.JOB_STAT_RUN:
                self.status = "Running"
            elif lsf.JOB_STAT_DONE:
                self.status = "Complete"
            elif lsf.JOB_STAT_EXIT:
                self.status = "Killed"
            elif lsf.JOB_STAT_USUSP:
                self.status = "Susp_person"
            elif lsf.JOB_STAT_SSUSP:
                self.status = "Susp_system"
            elif lsf.JOB_STAT_PEND:
                if j.pendStateJ == 0:
                    self.status = "Eligible"
                else:
                    self.status = "Blocked_system"
            elif lsf.JOB_STATE_PEND:
                self.status = "Blocked_person"
            else:
                self.status = "Unkown"
        else:
            self.status = "Unknown"


if __name__ == "__main__":
    connect.connect(queue="batch")
    if len(sys.argv) > 1:
        jobid = int(sys.argv[1])
    else:
        jobid = 0
    jobs = get_job_set(jobid=jobid, user="all", verbose=True, options=lsf.ALL_JOB)
    for j in jobs:
        stat = j.status
        jobid = j.jobId
        print(jobid, '\t', stat)

