# Drop all tables that have been used for testing.

SET FOREIGN_KEY_CHECKS=0;

DELETE FROM `test_rgt_test_event`;
DROP TABLE `test_rgt_test_event`;

DELETE FROM `test_rgt_test`;
DROP TABLE `test_rgt_test`;

DELETE FROM `test_rgt_event`;
DROP TABLE `test_rgt_event`;

DELETE FROM `test_rgt_check`;
DROP TABLE `test_rgt_check`;

SET FOREIGN_KEY_CHECKS=1;
