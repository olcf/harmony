# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class RgtCheck(models.Model):
    check_id = models.AutoField(primary_key=True)
    check_uid = models.SmallIntegerField(unique=True)
    check_desc = models.CharField(max_length=1024)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.check_uid} ({self.check_desc})'

    class Meta:
        managed = False
        db_table = 'rgt_check'
        ordering = ['check_uid']


class RgtEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    event_uid = models.SmallIntegerField(unique=True)
    event_name = models.CharField(max_length=256)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.event_uid} ({self.event_name})'

    class Meta:
        managed = False
        db_table = 'rgt_event'
        ordering = ['event_uid']


class RgtTest(models.Model):
    test_id = models.AutoField(primary_key=True)
    harness_uid = models.CharField(unique=True, max_length=36)
    harness_start = models.DateTimeField()
    harness_tld = models.CharField(max_length=1024)
    application = models.CharField(max_length=1024)
    testname = models.CharField(max_length=1024)
    job_id = models.CharField(max_length=64, blank=True, null=True)
    lsf_exit_status = models.SmallIntegerField(blank=True, null=True)
    build_status = models.SmallIntegerField(blank=True, null=True)
    submit_status = models.SmallIntegerField(blank=True, null=True)
    check_status = models.ForeignKey(RgtCheck, models.DO_NOTHING, db_column='check_status',
                                     to_field='check_uid', blank=True, null=True)
    output_build = models.TextField(blank=True, null=True)
    output_submit = models.TextField(blank=True, null=True)
    output_check = models.TextField(blank=True, null=True)
    output_report = models.TextField(blank=True, null=True)
    system = models.CharField(max_length=64)
    previous_job_id = models.CharField(max_length=36)
    done = models.BooleanField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.application} {self.testname} {self.harness_uid}'

    class Meta:
        managed = False
        db_table = 'rgt_test'
        ordering = ['application', 'testname', 'harness_uid']


class RgtTestEvent(models.Model):
    id = models.AutoField('id', primary_key=True)
    # These are renamed so that they query correctly. Otherwise it thinks that the '_id' is an addition by django.
    # The column is named 'test_id' so that '_id' is not auto appended.
    test_id = models.ForeignKey(RgtTest, models.DO_NOTHING, db_column='test_id')
    event_id = models.ForeignKey(RgtEvent, models.DO_NOTHING, db_column='event_id')
    event_time = models.DateTimeField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.test_id} {self.event_id}'

    class Meta:
        managed = False
        db_table = 'rgt_test_event'
        unique_together = (('test_id', 'event_id'),)
        ordering = ['test_id', 'event_id']


class TestRgtCheck(models.Model):
    check_id = models.AutoField(primary_key=True)
    check_uid = models.SmallIntegerField(unique=True)
    check_desc = models.CharField(max_length=1024)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.check_uid} ({self.check_desc})'

    class Meta:
        managed = False
        db_table = 'test_rgt_check'
        ordering = ['check_uid']


class TestRgtEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    event_uid = models.SmallIntegerField(unique=True)
    event_name = models.CharField(max_length=256)
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.event_uid} ({self.event_name})'

    class Meta:
        managed = False
        db_table = 'test_rgt_event'
        ordering = ['event_uid']


class TestRgtTest(models.Model):
    test_id = models.AutoField(primary_key=True)
    harness_uid = models.CharField(unique=True, max_length=36)
    harness_start = models.DateTimeField()
    harness_tld = models.CharField(max_length=1024)
    application = models.CharField(max_length=1024)
    testname = models.CharField(max_length=1024)
    job_id = models.CharField(max_length=64, blank=True, null=True)
    lsf_exit_status = models.SmallIntegerField(blank=True, null=True)
    build_status = models.SmallIntegerField(blank=True, null=True)
    submit_status = models.SmallIntegerField(blank=True, null=True)
    check_status = models.ForeignKey(TestRgtCheck, models.DO_NOTHING, db_column='check_status',
                                     to_field='check_uid', blank=True, null=True)
    output_build = models.TextField(blank=True, null=True)
    output_submit = models.TextField(blank=True, null=True)
    output_check = models.TextField(blank=True, null=True)
    output_report = models.TextField(blank=True, null=True)
    system = models.CharField(max_length=64)
    previous_job_id = models.CharField(max_length=36)
    done = models.IntegerField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.application} {self.testname} {self.harness_uid}'

    class Meta:
        managed = False
        db_table = 'test_rgt_test'
        ordering = ['application', 'testname', 'harness_uid']


class TestRgtTestEvent(models.Model):
    id = models.AutoField(primary_key=True)
    test_id = models.ForeignKey(TestRgtTest, models.DO_NOTHING, db_column='test_id')
    event_id = models.ForeignKey(TestRgtEvent, models.DO_NOTHING, db_column='event_uid')
    event_time = models.DateTimeField()
    timestamp = models.DateTimeField()

    def __str__(self):
        return f'{self.test_id} {self.event_id}'

    class Meta:
        managed = False
        db_table = 'test_rgt_test_event'
        unique_together = (('test_id', 'event_id'),)
        ordering = ['test_id', 'event_id']

