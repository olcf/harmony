# This is used to monitor some job.
from scripts import job_status
import time
import threading


class JobMonitor:
    """
    Class to setup monitoring of a set of jobs.
    """
    def __init__(self, max_monitors=100):
        """
        Constructor.

        :param max_monitors: Maximum number of jobs that can be monitored.
        Each job monitor creates a mostly dead thread that comes alive every once in a while.
        """
        self.running_monitors = []
        self.max_monitors = max_monitors

    def monitor_jobs(self, job_ids, watch_time, notifier, **kwargs):
        """
        Input either a single job or a list of jobs with some notification setup
        and begin monitoring jobs.

        :param job_ids: one or multiple ids of jobs to monitor.
        :param watch_time: How often the thread should wake for this set of jobs.
        :param notifier: Function that takes in key word arguments to send off.
        :param kwargs: Everything that the notifier needs.
        :return:
        """
        # Test if we have an int instead of a list and if so, turn it into a list.
        if type(job_ids) is int:
            job_ids = [job_ids]

        # Create a list of new threads that will begin monitoring jobs.
        new_monitors = []
        for job_id in job_ids:
            # Create the new threads.
            thread = threading.Thread(target=monitor, args=(job_id, watch_time, notifier),
                                      name=str(job_id) + "_job_monitor", kwargs=kwargs)
            # Add them to the list.
            new_monitors.append(thread)

        # Start all of the new monitors.
        for tup in new_monitors:
            tup.start()

        # Add all of the new monitors to the total and remove all threads that are done.
        self.running_monitors.extend(new_monitors)
        self.running_monitors = remove_dead_threads(self.running_monitors)

        # Check that we do not have too many threads.
        if len(self.running_monitors) > self.max_monitors:
            raise OverflowError("Too many job monitors!")

    def refresh_threads(self):
        """
        Remove all monitors that are done.
        :return:
        """
        self.running_monitors = remove_dead_threads(self.running_monitors)


def remove_dead_threads(thread_list):
    """
    Take in a list of threads and remove all done ones.
    :param thread_list: A list of threads.
    :return: A list of alive threads.
    """
    return [thread for thread in thread_list if thread.isAlive()]


def monitor(job_id, watch_time, notifier, num_iterations=None, **kwargs):
    """
    Monitor some job and notify whenever the status changes.

    :param job_id: id to monitor.
    :param watch_time: How often to recheck.
    :param notifier: Method to notify.
    :param num_iterations: If a job should only be monitored a certain number of times, this should be set.
    :param kwargs: Any arguments needed for the notifier.
    :return:
    """
    # Get the current status of the job.
    JS = job_status.JobStatus()
    # Try to get the jobs status but if it does not exist, notify and exit.
    try:
        status = JS.get_job_status(job_id)
    except KeyError as e:
        notifier(**kwargs, error_message=str(e))
        return

    # Remove class since we will have many of these threads and we want to relieve memory and not store this class.
    del JS

    done_stats = ['complete', 'killed', 'walltimed']
    done_stats = [job_status.Job.possible_status[stat] for stat in done_stats]

    if status in done_stats:
        done_status = True
    else:
        done_status = False

    # Notify about the current job's status.
    notifier(**kwargs, job_id=job_id, status=status, done=done_status)
    del done_status

    # Create an iteration counter.
    iteration = 0
    # While the job has not been completed, keep watching.
    while status not in done_stats:
        # Sleep the desired time.
        time.sleep(watch_time)

        # Find the new status of the job.
        JS = job_status.JobStatus()
        try:
            new_status = JS.get_job_status(job_id)
        except KeyError as e:
            notifier(**kwargs, job_id=job_id,
                     error_message="Something happened while monitoring my job. It seemed to disappear!\t" + str(e))
            return
        if new_status is None:
            notifier(**kwargs, job_id=job_id,
                     error_message="Something happened while monitoring my job. It seemed to disappear!\t" + str(e))
            return

        # If the status has changed then notify.
        if new_status != status:
            notifier(**kwargs, job_id=job_id, status=status, new_status=new_status)

            status = new_status

        # If we care about how many times we check then do so.
        if num_iterations is not None:
            iteration += 1
            if iteration >= num_iterations:
                break

        # Remove excess variables.
        del new_status
        del JS

    if status in done_stats:
        done_status = True
    else:
        done_status = False

    # Notify that the job is all done.
    notifier(**kwargs, job_id=job_id, status=status, done=done_status)

