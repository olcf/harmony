import pymysql


class DatabaseConnector:
    """
    Class to hold info on some connection.
    """
    def __init__(self, host, user, password, database_name):
        """
        Class to easily connect and disconnect some database.

        :param host: The host for the connection. (ex. 'localhost')
        :param user: The user trying to connect.
        :param password: The password for the user.
        :param database_name: The database targeted.
        """

        self.host = host
        self.user = user
        self.password = password
        self.database_name = database_name

    def connect(self):
        """
        Connect to some database.
        :return: The database that is connected to.
        """
        return pymysql.connect(self.host, self.user, self.password, self.database_name)
