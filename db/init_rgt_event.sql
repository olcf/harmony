
USE rgt;

INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (110, 'logging_start');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (120, 'build_start');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (130, 'build_end');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (140, 'submit_start');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (150, 'submit_end');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (160, 'job_queued');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (170, 'binary_execute_start');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (180, 'binary_execute_end');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (190, 'check_start');
INSERT IGNORE INTO rgt_event (event_uid, event_name) VALUES (200, 'check_end');
