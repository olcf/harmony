from scripts import job_status
from pythonlsf import lsf
import unittest
from random import randint
import os
from unit_tests import get_actual_jobs


class TestJobClass(unittest.TestCase):
    """
    Class to test the Job class in job_status.
    """

    def test_job_class(self):
        """
        Test whether one can create a Job and it has the correct properties.
        """
        # Open all possible stats that a job might have. The zero as the final stat acts as an unknown status.
        stats = [lsf.JOB_STAT_RUN, lsf.JOB_STAT_DONE, lsf.JOB_STAT_EXIT,
                 lsf.JOB_STAT_USUSP, lsf.JOB_STAT_SSUSP, lsf.JOB_STAT_PEND, 0]
        # Create two possibilities of exit codes. The first is a random job exit code while the second is a code
        # similar to what lsf pops out when a job hits it's walltime.
        exit_stats = [randint(1, 139), 140+(256*randint(1, 139))]
        # Either it is or is not pending.
        pend_states = [0, randint(1, 100)]
        # Give it a random job id.
        jobID = randint(1, 1000000)
        # Give it a name.
        jName = "practice_test_"

        # These are the expected stats that will come from the class.
        # They line up with the iterations through the lists.
        expected_stats = ["Running", "Running", "Running", "Running",
                          "Complete", "Complete", "Complete", "Complete",
                          "Killed", "Killed", "Walltimed", "Walltimed",
                          "Susp_person_dispatched", "Susp_person_dispatched", "Susp_person_dispatched", "Susp_person_dispatched", 
                          "Susp_system","Susp_system","Susp_system","Susp_system",
                          "Eligible", "Blocked", "Eligible", "Blocked",
                          "Unknown", "Unknown", "Unknown", "Unknown"]

        # Keep track of which stat to expect.
        index = 0
        # Iterate over the different job stats.
        for status in stats:
            # Iterate over possible exit stats.
            for exit_status in exit_stats:
                # Iterate over possible pending states.
                for pend_state_j in pend_states:
                    job_name = jName + str(index)
                    # Create a fake lsf job with the correct attributes.
                    lsf_job = TestJobClass.example_job(jobID=jobID, status=status, jName=job_name,
                                                       exit_status=exit_status, pend_state_j=pend_state_j)
                    # Create a job from the fake lsf job.
                    job = job_status.Job(lsf_job)
                    # Do subTests so that if it fails in one place it will still continue and try all.
                    with self.subTest(status=status, exit_status=exit_status, pend_state_j=pend_state_j):
                        # Assert that jobid is preserved.
                        self.assertEqual(job.jobId, jobID)
                        # Assert that the correct status from the class is given.
                        self.assertEqual(job.status, expected_stats[index])
                        # Assert that the name is preserved.
                        self.assertEqual(job.jobName, job_name)
                    # Move to the next expected status.
                    index += 1

    class example_job:
        """
        Class to create a fake lsf job for testing.
        """
        def __init__(self, jobID, jName, status, exit_status, pend_state_j):
            """
            Initialize the fake job.

            :param jobID: (int) The jobs id.
            :param status: (int) The lsf code status for the job.
            :param exit_status: (int) The lsf code status for exiting.
            :param pend_state_j: (int) The code for if it is pending.
            """
            self.jobId = jobID
            self.status = status
            self.exitStatus = exit_status
            self.pendStateJ = pend_state_j
            self.jName = jName


class TestJobStatus(unittest.TestCase):
    """
    Test that the job status finding aspect of job_status works correctly.
    """

    def setUp(self):
        """
        Set up variables for use later on in the code.
        """
        # Set the path where to get the currently running lsf jobs.
        bjobs_path = os.path.join(os.path.dirname(__file__), 'test_inputs')
        # Get the current lsf jobs into a file.
        get_actual_jobs.bjobs_to_file(bjobs_path)
        # Parse the file and get the results into a classwide variable.
        self.job_dics = get_actual_jobs.parse_bjobs(os.path.join(bjobs_path, 'example_bjobs.txt'))

        # Create a classwide variable for anything to do with job status.
        self.JS = job_status.JobStatus()

        # Dictionary to transform a jobstat to what would be returned by bjobs on lsf.
        self.jobstat_to_bjobstat = {'Running': 'RUN',
                                    'Complete': 'DONE',
                                    'Walltimed': 'EXIT', 'Killed': 'EXIT',
                                    'Susp_person_dispatched': 'USUSP',
                                    'Susp_person_pend': 'PSUSP',
                                    'Susp_system': 'SSUSP',
                                    'Eligible': 'PEND', 'Blocked': 'PEND'}

    def test_in_queue(self):
        """
        Test the in_queue method.
        """
        # Iterate over all jobs currently in lsf.
        for job_dic in self.job_dics:
            # If it is either running or pending then it should count as in queue.
            if job_dic['stat'] in ['RUN', 'PEND']:
                self.assertTrue(self.JS.in_queue(job_dic['jobid']))
            # Otherwise it is not in the queue.
            elif job_dic['stat'] in ['DONE', 'EXIT']:
                self.assertFalse(self.JS.in_queue(job_dic['jobid']))

    def test_get_jobs(self):
        """
        Test the get_jobs method.
        """
        # Get all jobs in lsf using our code.
        jobs = self.JS.get_jobs()
        # Iterate over all jobs found.
        for job in jobs:
            # Get the job in bjobs that matches.
            job_dics = self.find_job_dics_by_attr(attr_name='jobid', search_val=job.jobId)
            # Make sure that the status and id are equal.
            for job_dic in job_dics:
                self.assertEqual(job.jobId, job_dic['jobid'])
                self.assertEqual(self.jobstat_to_bjobstat[job.status], job_dic['stat'])

    def test_get_jobs_by_status(self):
        """
        Test the get_jobs_by_status method.
        """
        # Get all possible viable job states.
        viable_stats = job_status.Job.get_viable_status()
        # Iterate over these states.
        for stat in viable_stats:
            # Get all the jobs that match that state.
            jobs = self.JS.get_jobs_by_status(status=stat)
            # For each of those jobs, assert that there is a matching job in bjobs
            # and that each job does have the correct state.
            for job in jobs:
                with self.subTest(stat=stat):
                    job_dic = self.find_job_dics_by_attr(attr_name='jobid', search_val=job.jobId)[0]
                    self.assertEqual(job_dic['jobid'], job.jobId)
                    self.assertEqual(self.jobstat_to_bjobstat[job.status], job_dic['stat'])
                    self.assertEqual(job.status, stat)

    def test_get_jobs_by_name(self):
        """
        Test the get_jobs_by_name method.
        """
        # Create a list of job names.
        names = []
        # Iterate over each job in bjobs.
        for job_dic in self.job_dics:
            # If that job has not yet been checked, add them to names.
            if job_dic['jobname'] not in names:
                names.append(job_dic['jobname'])
                name = job_dic['jobname']
            # Otherwise continue to the next job.
            else:
                continue

            # Get all jobs with that name with our code.
            jobs = self.JS.get_jobs_by_name(name)
            # Get all jobs with that name with bjobs.
            actual_jobs = self.find_job_dics_by_attr(attr_name='jobname', search_val=name)

            # Get the ids of each of the jobs we found.
            job_ids = [job.jobId for job in jobs]
            # Get the ids of each of the actual bjobs jobs.
            actual_job_ids = [actual_job['jobid'] for actual_job in actual_jobs]

            # For each of these jobs, make sure that the id matches.
            with self.subTest(job_name=name):
                for job in jobs:
                    self.assertIn(job.jobId, actual_job_ids)
                for actual_job_id in actual_job_ids:
                    self.assertIn(actual_job_id, job_ids)

    def test_get_jobs_by_user(self):
        """
        Test the get_jobs_by_user method.
        """
        # Create a list of users.
        users = []
        # Iterate over each job in bjobs.
        for job_dic in self.job_dics:
            # If that user has not yet been checked, add them to users.
            if job_dic['user'] not in users:
                users.append(job_dic['user'])
                user = job_dic['user']
            # Otherwise continue to the next job.
            else:
                continue

            # Get all the jobs by that user using our code.
            jobs = self.JS.get_jobs_by_user(user)
            # Get all the jobs by that user using bjobs.
            actual_jobs = self.find_job_dics_by_attr(attr_name='user', search_val=user)

            # Get the ids of each of the jobs we found.
            job_ids = [job.jobId for job in jobs]
            # Get the ids of each of the jobs bjobs found.
            actual_job_ids = [actual_job['jobid'] for actual_job in actual_jobs]

            # For each of these jobs, make sure that the id matches.
            with self.subTest(user=user):
                for job in jobs:
                    self.assertIn(job.jobId, actual_job_ids)
                for actual_job_id in actual_job_ids:
                    self.assertIn(actual_job_id, job_ids)

    def find_job_dics_by_attr(self, attr_name, search_val):
        """
        Get all jobs in bjobs according to a certain attribute.

        :param attr_name: (str) Name of attribute to search by.
        :param search_val: Values to test if the job shares them.
        :return: jobs: (list) Jobs that satisfied the requirements.
        """
        # Initially no jobs found.
        jobs = []
        # For each job in bjobs . . .
        for job_dic in self.job_dics:
            # If the possible search values is a list, check if the job has an attribute in that list.
            if type(search_val) is list:
                if job_dic[attr_name] in search_val:
                    jobs.append(job_dic)
            # Otherwise just check that it matches.
            else:
                if search_val == job_dic[attr_name]:
                    jobs.append(job_dic)
        # Return the final list of matching jobs.
        return jobs


# Run all tests in this file when the file is run.
if __name__ == '__main__':
    unittest.main()
