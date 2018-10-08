import unittest
from unit_tests import get_actual_jobs
import os
from scripts import job_monitor
import random
import time
from unit_tests import global_vars
import shutil


class TestMonitor(unittest.TestCase):
    """
    Class to test if a single monitor works.
    """
    def test_single_monitor(self):
        """
        Test a monitor works.
        :return:
        """
        # Get the actual jobs to some file.
        job_dics = get_actual_jobs.get_jobs()

        # Set the path to the monitor output.
        monitor_path = os.path.join(os.path.dirname(__file__), 'test_inputs',
                                    'notification_outputs', 'single_monitor.txt')
        # Create an empty file.
        with open(monitor_path, mode="w+") as f:
            f.write("")

        # Set the neccessary parameters for the notifier.
        watch_time = 1
        # The notifier appends to the file we previously cleaned.
        notifier = monitor_to_file
        user = "test_user"
        num_iterations = 4

        # If there are jobs then we can try to monitor one of them.
        if len(job_dics) != 0:
            # Choose a random job so that this test case can easily be rerun and will choose different jobs to test.
            job_dic = job_dics[random.randint(0, len(job_dics) - 1)]
        # Otherwise we can not.
        else:
            self.skipTest("There are no jobs in LSF that could be tested for monitoring.")

        # Get the id and status of the randomly chosen job.
        job_id = job_dic['jobid']
        old_status = job_dic['stat']

        # Monitor the job. This will take watch_time * num_iterations seconds.
        job_monitor.monitor(job_id=job_id, watch_time=watch_time, notifier=notifier, user=user,
                            path=monitor_path, num_iterations=num_iterations)

        # Get the contents output from the notifier.
        with open(monitor_path, mode='r') as f:
            contents = [line.strip() for line in f]

        # Get the currently running jobs.
        updated_job_dics = get_actual_jobs.get_jobs()

        # Find the job in LSF that corresponds to the job we started with.
        for job in updated_job_dics:
            if job['jobid'] == job_id:
                updated_job_dic = job
                break
        else:
            self.skipTest("The test the was being monitored disappeared from LSF. job_id: " + str(job_id))

        # Get the status of the job after some time in lsf.
        new_status = updated_job_dic['stat']

        # Get the number of changes and the number of usable lines from the notifier output file.
        # Start at -1 since first END_OF_MESSAGE is just the current status.
        number_of_changes = -1
        usable_contents = []
        for line in contents:
            if "END_OF_MESSAGE" in line:
                number_of_changes += 1
                usable_contents.append(line)

        # There should be at least one message in the file.
        self.assertGreaterEqual(number_of_changes, 0)

        # Set a variable to hold whether the first notification (the current job status) has been read.
        found_starter = False
        # Create variable for holding the previous status of the job.
        previous_status = None
        # For each line in the file, check multiple items.
        for i in range(len(usable_contents)):
            line = usable_contents[i]
            # Create a subtest so each line can be tested without errors in between stopping everything.
            with self.subTest(line=line):
                if 'error_message' in line:
                    self.fail("I failed because of some error message in the file.\n" + line)
                # Assert that the necessary variables to test are set.
                self.assertIn('user', line)
                self.assertIn('job_id', line)
                self.assertIn('status', line)
                self.assertIn('done', line)

                # Split the line and get the indecies of each variable.
                split_line = line.split()
                user_index = split_line.index('user:') + 1
                # Assert the users are the same.
                self.assertEqual(split_line[user_index], user)
                job_id_index = split_line.index('job_id:') + 1
                # Assert that the job ids are the same.
                self.assertEqual(int(split_line[job_id_index]), job_id)

                status_index = split_line.index('status:') + 1
                done_index = split_line.index('done:') + 1
                # If we have not found the first update from the monitor then this is it.
                # The first line should contain the information of the old status of the job.
                if not found_starter:
                    # Make sure starting status is the same.
                    self.assertEqual(global_vars.jobstat_to_bjobstat[split_line[status_index]], old_status)
                    found_starter = True
                else:
                    # If the status has changed, the previous status is called 'status' in our notifier.
                    self.assertEqual(split_line[status_index], previous_status)

                # Set the previous status as the current status.
                previous_status = split_line[status_index]

                # Test if this is a line that contains an update.
                if i > 0 and i != len(usable_contents) - 1:
                    # Make sure that an update has a new status.
                    self.assertIn('new_status', line)

                    # Get the index of the new_status.
                    new_status_index = split_line.index('new_status:') + 1
                    # Assert that the new status and the previous status are not the same.
                    self.assertNotEqual(split_line[status_index], split_line[new_status_index])

                # Test if the current line is the last line in the file and is not the starter.
                elif found_starter and i == len(usable_contents) - 1:
                    # Assert that the current LSF status of the job is the same as the final recorded by the monitor.
                    self.assertEqual(global_vars.jobstat_to_bjobstat[split_line[status_index]], new_status)

                    # If the status was finished then the expected state of the monitor should be done.
                    if new_status in ['DONE', 'EXIT']:
                        expected_done_state = True
                    else:
                        expected_done_state = False
                    # Assert that this the monitor knew it should be done or not.
                    self.assertEqual(split_line[done_index], str(expected_done_state))


def monitor_to_file(user=None, job_id=None, status=None, new_status=None, path=None, done=False, error_message=None):
    """
    Take in multiple parameters and create a message for some file.

    :param user: User to pretend to notify.
    :param job_id: Job id that was recorded.
    :param status: The status of the job currently or the status the job is changing from.
    :param new_status: The new status of the job.
    :param path: The path to the file to write to.
    :param done: Whether the monitor is all done with the job.
    :param error_message: Record any error messages needed.
    :return:
    """
    # If path is not set, we can not do anything.
    if path is None:
        raise Exception("I don't know where to write to.")

    # If there is no error message and not enough info given then the message is not recorded.
    # If there is an error message we want to record it.
    if error_message is None:
        if user is None or job_id is None or status is None:
            raise Exception('There was not enough information to create a message.')

        # Create the initial message.
        message = "user: " + user + " job_id: " + str(job_id) + " status: " + status
        # If there is a new_status then this is an update and record the new status.
        if new_status is not None:
            message += " new_status: " + new_status

        # Add whether the monitor is done and that this is the end of the message.
        message += " done: " + str(done) + " END_OF_MESSAGE \n"
    else:
        message = "error_message: " + error_message + " END_OF_MESSAGE \n"

    # If there are multiple paths input that could be written to, match the one that contains this job's id.
    if type(path) is list:
        # Search the paths for the correct one.
        for p in path:
            if str(job_id) in p:
                path = p
                break
        else:
            raise FileNotFoundError("Could not find file to write job " + str(job_id) + " to.")
    # Add the message to the file.
    append_to_file(message, path)


def append_to_file(text, path):
    """
    Append some text to some file.

    :param text: Text to add to the file.
    :param path: Path to file to write to.
    :return:
    """
    with open(path, mode='a+') as f:
        f.write(text)


class TestJobMonitorClass(unittest.TestCase):
    """
    Test if multiple jobs can be monitored at once.
    """
    def test_monitor_class(self):
        """
        Test if the class functions correctly and monitors jobs correctly.
        :return:
        """

        # Get the jobs currently in LSF.
        job_dics = get_actual_jobs.get_jobs()

        # Get all of the ids and stats.
        job_ids = [job_dic['jobid'] for job_dic in job_dics]
        old_stats = [job_dic['stat'] for job_dic in job_dics]
        # Create all the paths. Each path also contains the job id that is being monitored.
        monitor_folder_path = os.path.join(os.path.join(os.path.dirname(__file__), 
                                           'test_inputs', 'notification_outputs'))
        monitor_postfix = "_job_monitor.txt"
        monitor_paths = [os.path.join(monitor_folder_path, str(job_id) + monitor_postfix)
                         for job_id in job_ids]

        if not os.path.exists(monitor_folder_path):
            os.mkdir(monitor_folder_path)
        # Create/clear all of these files.
        for monitor_path in monitor_paths:
            with open(monitor_path, mode="w") as f:
                f.write("")

        # Set all variables for the monitors.
        watch_time = 1
        notifier = monitor_to_file
        user = "test_user"
        num_iterations = 4

        # If there are no jobs then skip this test.
        if len(job_dics) == 0:
            self.skipTest("There are no jobs in LSF that could be tested for monitoring.")

        # Create our monitor.
        JM = job_monitor.JobMonitor()
        # Let it start monitoring the jobs. Since this takes a very short time to start the threads, we need to force
        # this test to wait.
        JM.monitor_jobs(job_ids=job_ids, watch_time=watch_time, notifier=notifier, user=user,
                        path=monitor_paths, num_iterations=num_iterations)
        time.sleep(num_iterations * watch_time)

        # Get the status of the jobs now.
        updated_job_dics = get_actual_jobs.get_jobs()

        # Get all jobs that match a job_id we had previously.
        useful_job_dics = []
        for job in updated_job_dics:
            if job['jobid'] in job_ids:
                useful_job_dics.append(job)

        # If we have no useful jobs in lsf anymore then we exit the test.
        if len(useful_job_dics) == 0:
            self.skipTest("There are no jobs in LSF that could be tested for monitoring.")

        # For each of the new jobs check that they were correctly monitored.
        for updated_job_dic in useful_job_dics:
            # Get the info from the updated job.
            job_id = updated_job_dic['jobid']
            old_status = old_stats[job_ids.index(job_id)]
            # Get the path to where this job was monitored.
            monitor_path = monitor_paths[job_ids.index(job_id)]
            # Get the files contents.
            with open(monitor_path, mode='r') as f:
                contents = [line.strip() for line in f]

            # Find the status of the job from LSF.
            new_status = updated_job_dic['stat']

            # Get all the contents in the file that the monitor sent to that are important.
            # Start at -1 since first END_OF_MESSAGE is just the current status.
            number_of_changes = -1
            usable_contents = []
            for line in contents:
                if "END_OF_MESSAGE" in line:
                    number_of_changes += 1
                    usable_contents.append(line)

            # There should be at least one message in the file.
            self.assertGreaterEqual(number_of_changes, 0)

            # Everything else is the same tests as the 'test_single_monitor' test found above.
            found_starter = False
            previous_status = None
            for i in range(len(usable_contents)):
                line = usable_contents[i]
                with self.subTest(line=line):
                    self.assertIn('user', line)
                    self.assertIn('job_id', line)
                    self.assertIn('status', line)
                    self.assertIn('done', line)

                    split_line = line.split()
                    user_index = split_line.index('user:') + 1
                    self.assertEqual(split_line[user_index], user)
                    job_id_index = split_line.index('job_id:') + 1
                    self.assertEqual(int(split_line[job_id_index]), job_id)
                    status_index = split_line.index('status:') + 1
                    done_index = split_line.index('done:') + 1
                    # If we have not found the first update from the monitor then this is it.
                    # The first line should contain the information of the old status of the job.
                    if not found_starter:
                        self.assertEqual(global_vars.jobstat_to_bjobstat[split_line[status_index]], old_status)
                        if old_status in ['DONE', 'EXIT']:
                            expected_done_state = True
                        else:
                            expected_done_state = False
                        self.assertEqual(split_line[done_index], str(expected_done_state))
                        found_starter = True
                    else:
                        self.assertEqual(split_line[status_index], previous_status)

                    previous_status = split_line[status_index]

                    # Test if this is a line that contains an update.
                    if i > 0 and i != len(usable_contents) - 1:
                        self.assertIn('new_status', line)

                        new_status_index = split_line.index('new_status:') + 1
                        self.assertNotEqual(split_line[status_index], split_line[new_status_index])

                    # Test if the current line is the last line in the file.
                    elif i > 0 and i == len(usable_contents) - 1:
                        self.assertEqual(global_vars.jobstat_to_bjobstat[split_line[status_index]], new_status)
                        if new_status in ['DONE', 'EXIT']:
                            expected_done_state = True
                        else:
                            expected_done_state = False
                        self.assertEqual(split_line[done_index], str(expected_done_state))

        # Remove all files created for monitoring.
        for f in os.listdir(monitor_folder_path):
            if monitor_postfix in f:
                os.remove(os.path.join(monitor_folder_path, f))

