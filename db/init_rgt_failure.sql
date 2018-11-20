
USE rgt;

INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Self-inflicted: submit failure');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Self-inflicted: build failure');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Build timed out');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Build failed');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('GPU busy error');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Job step hang');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Job step failure');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Self-Inflicted: Killed job');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Lingering processes');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Node failure');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Self-Inflicted: Job script bug');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Performance Failure');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('PMIx crash');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Software Environment Issue');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Unknown');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Job Walltimed');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Error with job submission wrapper');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('False Positive');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('CUDA error');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('Incorrect answer');
INSERT IGNORE INTO rgt_failure (failure_label) VALUES ('File system problem');
