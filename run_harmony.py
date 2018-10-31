from scripts.database import update_database
from scripts import config_functions
import argparse
import time
from scripts.database import connect_database
import traceback


def create_parser():
    """
    Create a parser for getting the necessary options when running the database.
    :return: The parser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--rgt-path', dest='rgt_path', help='Path to the rgt input file.')
    parser.add_argument('-u', '--user', dest='user', help='User on the database to act as.')
    parser.add_argument('-p', '--password', dest='password', help='Password for the user.')

    return parser


def run():
    """
    Run harmony.
    """
    # Create a parser and get the arguments.
    parser = create_parser()
    args = parser.parse_args()

    # Write the config file.
    config_functions.write_config(user=args['user'], password=args['password'])

    # Get the written database config.
    database = config_functions.get_config()['database']
    # Continue updating infinitely.
    while True:
        start = time.time()
        # Create necessary variables.
        connector = connect_database.DatabaseConnector()
        rgt_input_path = args['rgt_path']
        test_table = database['test_table']
        test_event_table = database['test_event_table']
        event_table = database['event_table']

        # Update the database.
        UD = update_database.UpdateDatabase(connector, rgt_input_path, test_table=test_table,
                                            test_event_table=test_event_table, event_table=event_table)
        try:
            UD.update_tests()
        except Exception:
            traceback.print_exc()

        del UD

        total_time = time.time() - start
        # Either immediately refresh if the time it took to update took longer than the refresh time
        # or sleep for the remaining refresh period.
        time.sleep(max(database['refresh_time'] - total_time, 0))


if __name__ == '__main__':
    run()
