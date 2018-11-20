from os import path as p
import pymysql
import warnings


check_path = p.abspath(p.join(p.dirname(__file__), '..', '..', 'db', 'init_rgt_check.sql'))
event_path = p.abspath(p.join(p.dirname(__file__), '..', '..', 'db', 'init_rgt_event.sql'))
failure_path = p.abspath(p.join(p.dirname(__file__), '..', '..', 'db', 'init_rgt_failure.sql'))


def insert_default(connector, default_check_path=check_path,
                   default_event_path=event_path, default_failure_path=failure_path):
    """
    Set the initial values for the various tables.

    :param connector: A DatabaseConnector for access to the database.
    :param default_check_path: The path to the default check values.
    :param default_event_path: The path to the default event values.
    :param default_failure_path: The path to the default failure values.
    """
    execute_sql_file(connector, default_check_path)
    execute_sql_file(connector, default_event_path)
    execute_sql_file(connector, default_failure_path)


def create_db(connector, file_path=p.abspath(p.join(p.dirname(__file__), '..', '..', 'db', 'create.sql'))):
    """
    Create the initial tables in the database.

    :param connector: A DatabaseConnector for access to the database.
    :param file_path: The path to the create file.
    """
    execute_sql_file(connector, file_path)


def execute_sql_file(connector, file_path, verbose=False):
    """
    Input the path to some .sql file and run it.

    :param connector: The connector to connect to the database.
    :param file_path: Path to the file.
    :param verbose: Whether to print out what is being run.
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
            print("Command skipped: " + command, e.args)
        except Exception as e:
            database.rollback()
            raise e
        else:
            database.commit()

    # Close the connection.
    database.close()

