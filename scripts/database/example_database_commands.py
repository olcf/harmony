import pymysql
from scripts.database import connect_database

if __name__ == '__main__':
    DC = connect_database.DatabaseConnector('localhost', 'root', 'password', 'harmony')
    db = DC.connect()
    cursor = db.cursor()
    sql = "SELECT test_id FROM testing_table WHERE done = FALSE "
    cursor.execute(sql)
    print(cursor.fetchone()[0])