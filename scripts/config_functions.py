import configparser
import os
import sys


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))


def previous_database_info(file_path):
    """
    Get the previous user and password for the database so that it only needs to be entered once
    when making the config file.

    :param file_path: Path to the config file.
    :return: The user and password found in the config file.
    """
    previous_conf = get_config(file_path)
    if len(previous_conf) == 0:
        return None, None
    database = previous_conf['DATABASE']

    user = database['user']
    password = database['password']

    return user, password


def write_config(file_path=config_path, user=None, password=None):
    """
    Write the config file for harmony.

    :param file_path: The path to where the config file will be.
    :param password: The password to the database.
    :param user: The user for the database.
    """
    conf = configparser.ConfigParser()

    # SLACK_APP
    conf['SLACK_APP'] = {}
    slack_app = conf['SLACK_APP']
    slack_app['SLACK_BOT_TOKEN'] = os.environ['SLACK_BOT_TOKEN']
    slack_app['SLACK_APP_TOKEN'] = os.environ['SLACK_APP_TOKEN']
    slack_app['SLACK_HARMONY_CHANNEL'] = os.environ['SLACK_HARMONY_CHANNEL']
    # How often to pull from slack.
    slack_app['WATCH_TIME'] = '1.0'
    # Maximum number of threads open that are trying to message.
    slack_app['MAX_MESSENGERS'] = '4'
    # Maximum number of messages to read from slack before trying to send any.
    slack_app['MAX_READS'] = '100'
    # Maximum length of some message that will be parsed.
    slack_app['MAX_MESSAGE_LENGTH'] = '100'
    # Maximum number of keys in that are allowed in a message.
    slack_app['MAX_MESSAGE_KEYS'] = '20'

    # DATABASE
    conf['DATABASE'] = {}
    database = conf['DATABASE']

    database['HOST'] = 'rgtroute-stf006.marble.ccs.ornl.gov'
    database['PORT'] = '31673'
    database['DATABASE_NAME'] = 'rgt'
    # Get the previous username and password so that it is preserved if someone wants to rewrite the config file
    # without adding the user and password options.
    prev_user, prev_password = previous_database_info(config_path)
    if user is None:
        database['USER'] = prev_user
    else:
        database['USER'] = user

    if password is not None:
        database['PASSWORD'] = prev_password
    else:
        database['PASSWORD'] = password

    database['TEST_TABLE'] = 'rgt_test'
    database['EVENT_TABLE'] = 'rgt_event'
    database['CHECK_TABLE'] = 'rgt_check'
    database['TEST_EVENT_TABLE'] = 'rgt_test_event'

    # Refresh the database every half hour.
    database['REFRESH_TIME'] = '1800'

    # Maximum length of a message we send.
    # Slack splits it into multiple bits when it is longer than ~4000 so this is a good limit.
    database['MAX_SENT_MESSAGE_LENGTH'] = '3500'

    with open(file_path, mode='w+') as configfile:
        conf.write(configfile)


def get_config(file_path=config_path):
    """
    Get the config file.

    :param file_path: Path to the config file.
    :return: The config file after parsing.
    """
    conf = configparser.ConfigParser()

    conf.read(file_path)
    return conf


if __name__ == '__main__':
    if len(sys.argv) > 1:
        password = sys.argv[1]
        write_config(config_path=config_path, password=password)

    else:
        write_config(config_path=config_path)
