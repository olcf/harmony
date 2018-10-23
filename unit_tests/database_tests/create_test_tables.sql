# Create example tables for testing the database.

# Hold different types of events.
CREATE TABLE IF NOT EXISTS `test_rgt_event`
  (
  `event_id`          INT (6)         AUTO_INCREMENT,
  `event_uid`         SMALLINT        NOT NULL,
  `event_name`        VARCHAR (256)   NOT NULL,
  `timestamp`         TIMESTAMP       ,
  PRIMARY KEY ( `event_id` ),
  UNIQUE  KEY `event_uid`  ( `event_uid` )
  );

# Information about error types when checking LSF.
CREATE TABLE IF NOT EXISTS `test_rgt_check`
  (
  `check_id`          INT (6)         AUTO_INCREMENT,
  `check_uid`         TINYINT         NOT NULL,
  `check_desc`        VARCHAR (1024)  NOT NULL,
  `timestamp`         TIMESTAMP       ,
  PRIMARY KEY ( `check_id` ),
  UNIQUE KEY  `check_uid` ( `check_uid` )
  );

# Hold info about test.
CREATE TABLE IF NOT EXISTS `test_rgt_test`
  (
  `test_id`           INT (6)         AUTO_INCREMENT,
  `harness_uid`       CHAR (36)       NOT NULL,
  `harness_start`     DATETIME        NOT NULL,
  `harness_tld`       VARCHAR (1024)  NOT NULL,
  `application`       VARCHAR (1024)  NOT NULL,
  `testname`          VARCHAR (1024)  NOT NULL,
  `job_id`            CHAR (64)       NULL,
  `lsf_exit_status`   TINYINT         NULL,
  `build_status`      TINYINT         NULL,
  `submit_status`     TINYINT         NULL,
  `check_status`      TINYINT         NULL,
  `output_build`      TEXT            NULL,
  `output_submit`     TEXT            NULL,
  `output_check`      TEXT            NULL,
  `output_report`     TEXT            NULL,
  `system`            VARCHAR (64)    NOT NULL,
  `next_harness_uid`  CHAR (36)       NOT NULL,
  `done`              BOOLEAN         NOT NULL,
  `timestamp`         TIMESTAMP       ,
  PRIMARY KEY  ( `test_id` ),
  UNIQUE  KEY `harness_uid`  ( `harness_uid` ),
  FOREIGN KEY ( `check_status` ) REFERENCES `test_rgt_check` ( `check_uid` )
  );

# Hold ids of events that occurred to tests.
CREATE TABLE IF NOT EXISTS `test_rgt_test_event`
  (
  `id`                INT (6)         AUTO_INCREMENT,
  `test_id`           INT (6)         NOT NULL,
  `event_id`          INT (6)         NOT NULL,
  `event_time`        DATETIME        NOT NULL,
  `timestamp`         TIMESTAMP       ,
  PRIMARY KEY ( `id` ),
  FOREIGN KEY ( `test_id` ) REFERENCES `test_rgt_test` ( `test_id` ),
  FOREIGN KEY ( `event_id` ) REFERENCES `test_rgt_event` ( `event_id` ),
  UNIQUE  KEY `test_event` ( `test_id`, `event_id` )
  );
