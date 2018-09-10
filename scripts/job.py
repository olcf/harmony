"""Job class. """
from pythonlsf import lsf

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
				self.status = "Unknown"
		else:
			self.status = "Unknown"

		
			
