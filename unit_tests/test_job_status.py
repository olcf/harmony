from scripts import job_status
from pythonlsf import lsf
import unittest
from random import randint
import os


class TestJobClass(unittest.TestCase):
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
                    lsf_job = TestJobClass.example_job(jobID=jobID, status=status,
                                                     exit_status=exit_status, pend_state_j=pend_state_j)
                    Job = job_status.Job(lsf_job)
                    with self.subTest():
                        self.assertEqual(Job.jobId, jobID)
                        self.assertEqual(Job.status, expected_stats[index])
                    index += 1

    # Class for creating fake lsf jobs.
    class example_job:
        def __init__(self, jobID, status, exit_status, pend_state_j):
            self.jobID = jobID
            self.status = status
            self.exitStatus = exit_status
            self.pendStateJ = pend_state_j


class TestJobStatus(unittest.TestCase):
    def setUp(self):
        bjobs_path = os.path.join(__file__, 'test_inputs')
        self.bjobs_to_file(bjobs_path)
        self.job_dics = self.parse_bjobs(os.path.join(bjobs_path, 'example_bjobs.txt'))
        self.JS = job_status.JobStatus()
        self.jobstat_to_bjobstat = {'Running': 'RUN',
                                    'Complete': 'DONE',
                                    'Walltimed': 'EXIT', 'Killed': 'EXIT',
                                    'Susp_person': 'USUSP',
                                    'Susp_system': 'SSUSP',
                                    'Eligible': 'PEND', 'Blocked': 'PEND'}

    def test_in_queue(self):
        for job_dic in self.job_dics:
            if job_dic['stat'] in ['RUN', 'PEND']:
                self.assertTrue(self.JS.in_queue(job_dic['jobid']))
            elif job_dic['stat'] in ['DONE', 'EXIT']:
                self.assertFalse(self.JS.in_queue(job_dic['jobid']))

    def test_get_jobs(self):
        jobs = self.JS.get_jobs()
        for job in jobs:
            job_dic = self.find_job_dics_by_attr(attr_name='jobid', search_val=job.jobId)
            self.assertEqual(self.jobstat_to_bjobstat(job.status), job_dic['stat'])

    def test_get_jobs_by_status(self):
        viable_stats = job_status.Job.get_viable_status()
        for stat in viable_stats:
            jobs = self.JS.get_jobs_by_status(status=stat)
            for job in jobs:
                job_dic = self.find_job_dics_by_attr(attr_name='jobid', search_val=job.jobId)
                self.assertEqual(self.jobstat_to_bjobstat(job.status), job_dic['stat'])
                self.assertEqual(job.status, stat)

    def test_get_jobs_by_name(self):
        names = []
        for job_dic in self.job_dics:
            if job_dic['jobname'] not in names:
                names.append(job_dic['jobname'])
                name = job_dic['jobname']
            else:
                continue

            jobs = self.JS.get_jobs_by_name(name)
            actual_jobs = self.find_job_dics_by_attr(attr_name='jobname', search_val=name)

            actual_job_ids = [actual_job['job_id'] for actual_job in actual_jobs]

            for job in jobs:
                self.assertIn(job.jobId, actual_job_ids)

    def test_get_jobs_by_user(self):
        users = []
        for job_dic in self.job_dics:
            if job_dic['user'] not in users:
                users.append(job_dic['user'])
                user = job_dic['user']
            else:
                continue

            jobs = self.JS.get_jobs_by_user(user)
            actual_jobs = self.find_job_dics_by_attr(attr_name='user', search_val=user)

            actual_job_ids = [actual_job['user'] for actual_job in actual_jobs]

            for job in jobs:
                self.assertIn(job.jobId, actual_job_ids)

    def find_job_dics_by_attr(self, attr_name, search_val):
        jobs = []
        for job_dic in self.job_dics:
            if type(search_val) is list:
                if job_dic[attr_name] in search_val:
                    jobs.append(job_dic)
            else:
                if search_val == job_dic[attr_name]:
                    jobs.append(job_dic)
        return jobs

    def bjobs_to_file(self, bjobs_path):
        bjobs_command = os.path.join(bjobs_path, 'bjobs_to_file.sh')
        bjobs_file = os.path.join(bjobs_path, 'example_bjobs.txt')
        import subprocess
        subprocess.check_call([bjobs_command, bjobs_file])

    # Parse the output of 'bjobs -u all -a' that is in a file.
    def parse_bjobs(self, file_path):
        file_contents = []
        # Get file into list.
        for line in open(file_path):
            file_contents.append(line)

        variable_line = file_contents.pop(0)
        jobid_index = [variable_line.find('JOBID'), variable_line.find('USER')]
        user_index = [variable_line.find('USER'), variable_line.find('STAT')]
        stat_index = [variable_line.find('STAT'), variable_line.find('QUEUE')]
        jobname_index = variable_line.find('JOB_NAME')

        job_dics = []
        for line in file_contents:
            job_dics.append({'jobid': int(line[jobid_index[0]:jobid_index[1]].strip()),
                             'user': line[user_index[0]:user_index[1]].strip(),
                             'stat': line[stat_index[0]:stat_index[1]].strip(),
                             'jobname': line[jobname_index:]}.strip())

        return job_dics


if __name__ == '__main__':
    parse_bjobs('a', '/Users/cameronkuchta/Documents/Github/harmony/unit_tests/test_inputs/example_bjobs.txt')
