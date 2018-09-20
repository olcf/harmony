from scripts import job_status
from pythonlsf import lsf
import unittest
from random import randint


class TestJobStatus(unittest.TestCase):
    # Test whether one can create a Job and it has the correct properties.
    def test_job_class(self):
        stats = [lsf.JOB_STAT_RUN, lsf.JOB_STAT_DONE, lsf.JOB_STAT_EXIT,
                 lsf.JOB_STAT_USUSP, lsf.JOB_STAT_SSUSP, lsf.JOB_STAT_PEND, -1]
        exit_stats = [randint(1, 139), 140+(256*randint(1, 139))]
        pend_states = [0, randint(1, 100)]
        jobID = randint(1, 1000000)

        expected_stats = ["Running", "Running", "Running", "Running",
                          "Complete", "Complete", "Complete", "Complete",
                          "Walltimed", "Walltimed", "Killed", "Killed",
                          "Susp_person", "Susp_person", "Susp_person", "Susp_person",
                          "Susp_system","Susp_system","Susp_system","Susp_system",
                          "Eligible", "Blocked", "Eligible", "Blocked",
                          "Unknown", "Unknown", "Unknown", "Unknown"]
        index = 0
        for status in stats:
            for exit_status in exit_stats:
                for pend_state_j in pend_states:
                    lsf_job = TestJobStatus.test_job(jobID=jobID, status=status,
                                                     exit_status=exit_status, pend_state_j=pend_state_j)
                    Job = job_status.Job(lsf_job)
                    with self.subTest():
                        self.assertEqual(Job.jobId, jobID)
                        self.assertEqual(Job.status, expected_stats[index])
                    index += 1

    # Class for creating fake lsf jobs.
    class test_job:
        def __init__(self, jobID, status, exit_status, pend_state_j):
            self.jobID = jobID
            self.status = status
            self.exitStatus = exit_status
            self.pendStateJ = pend_state_j


if __name__ == '__main__':
    unittest.main()
