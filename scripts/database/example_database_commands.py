from scripts.database import connect_database
import os


if __name__ == '__main__':
    DC = connect_database.DatabaseConnector('localhost', 'root', 'password', 'harmony')
    db = DC.connect()
    cursor = db.cursor()
    sql = "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'harmony' AND TABLE_NAME = 'rgt_test'"
    cursor.execute(sql)
    print(cursor.fetchall())
    more_sql = "SELECT EXISTS(SELECT 1 FROM testing_table WHERE harness_uid = 1)"
    cursor.execute(more_sql)
    print(cursor.fetchone()[0])