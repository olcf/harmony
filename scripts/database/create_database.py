from os import path as p
import pymysql


def create_db(connector, file_path=p.abspath(p.join(p.dirname(__file__), '..', '..', 'db', 'create.sql'))):
    """
    Create the initial tables in the database.

    :param connector: A DatabaseConnector for access to the database.
    :param file_path: The path to the create file.
    :return:
    """
    execute_sql_file(connector, file_path)


def execute_sql_file(connector, file_path, verbose=False):
    """
    Input the path to some .sql file and run it.

    :param connector: The connector to connect to the database.
    :param file_path: Path to the file.
    :param verbose: Whether to print out what is being run.
    :return:
    """
    # Get the database from the connector.
    database = connector.connect()
    # Activate a cursor.
    cursor = database.cursor()

    # Open the file and get the lines.
    with open(file_path, mode='r') as f:
        sql_file = ""
        for line in f:
            if len(line.lstrip()) != 0 and line.lstrip()[0] != '#':
                cleaned_line = line.replace('\n', ' ')
                sql_file += cleaned_line + " "

    # Split according to ';' and try running commands.
    sql_commands = sql_file.split(';')

    # Remove dead lines.
    sql_commands = [command for command in sql_commands if len(command.strip()) != 0]

    for command in sql_commands:
        # Try to execute the command and if it does not work inform the user.
        # Otherwise commit the command to the database.
        if verbose:
            print("Running '" + command + "'")
        try:
            cursor.execute(command)
        except pymysql.MySQLError as e:
            print("Command skipped: ", e.args)
        except Exception as e:
            raise e
        else:
            database.commit()

    database.close()

