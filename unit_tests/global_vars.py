
# Dictionary to transform a jobstat to what would be returned by bjobs on lsf.
jobstat_to_bjobstat = {'Running': 'RUN',
                       'Complete': 'DONE',
                       'Walltimed': 'EXIT', 'Killed': 'EXIT',
                       'Susp_person_dispatched': 'USUSP',
                       'Susp_person_pend': 'PSUSP',
                       'Susp_system': 'SSUSP',
                       'Eligible': 'PEND', 'Blocked': 'PEND'}

