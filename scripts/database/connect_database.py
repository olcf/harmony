import pymysql
from scripts import config_functions


class DatabaseConnector:
    """
    Class to hold info on some connection.
    """

    def __init__(self, database_config, user=None, password=None):
        """
        Class to easily connect and disconnect some database.

        :param database_config: The config section for the database.
        """

        # Get important values from the config that will be used when connecting to the database.
        self.host = database_config['host']
        if user is None:
            self.user = database_config['user']
        else:
            self.user = user
        if password is None:
            self.password = database_config['password']
        else:
            self.password = password
        self.database_name = database_config['database_name']

        # The port is not necessarily needed but if it is set, use it.
        if 'port' in database_config:
            self.port = int(database_config['port'])
        else:
            self.port = None

    def connect(self):
        """
        Connect to some database.

        :return: The database that is connected to.
        """
        # If there is a port defined, use that. Otherwise use the default port.
        if self.port is not None:
            return pymysql.connect(self.host, self.user, self.password, self.database_name, port=self.port)
        else:
            return pymysql.connect(self.host, self.user, self.password, self.database_name)


if __name__ == '__main__':
    conf = config_functions.get_config()

    DC = DatabaseConnector(conf['host'], conf['user'], conf['password'], conf['database_name'])
    db = DC.connect()
    cursor = db.cursor()
    sql = "SELECT * FROM testing_table"
    cursor.execute(sql)
    print(cursor.fetchall())
