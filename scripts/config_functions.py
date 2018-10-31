import configparser
import os


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
slack_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'slack_tokens.txt'))
database_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database_tokens.txt'))


def write_config(path_to_config=config_path, path_to_slack_tokens=slack_path, path_to_database_tokens=database_path):
    """
    Write the config file for harmony.

    :param path_to_config: The path to where the config file will be.
    :param password: The password to the database.
    :param user: The user for the database.
    """
    conf = configparser.ConfigParser()

    # SLACK_APP
    conf['SLACK_APP'] = {}
    slack_app = conf['SLACK_APP']
    slack_tokens = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_HARMONY_CHANNEL']
    # The token file should have stuff that looks like SLACK_BOT_TOKEN = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # It does not necessarily look exactly like that though. Just split via space.
    with open(path_to_slack_tokens, mode='r') as f:
        for line in f:
            for token in slack_tokens:
                if line.upper().startswith(token):
                    line = line.split('=')
                    slack_app[token] = line[1].strip()
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
    database['TEST_TABLE'] = 'rgt_test'
    database['EVENT_TABLE'] = 'rgt_event'
    database['CHECK_TABLE'] = 'rgt_check'
    database['TEST_EVENT_TABLE'] = 'rgt_test_event'

    database_tokens = ['USER', 'PASSWORD']
    with open(path_to_database_tokens, mode='r') as f:
        for line in f:
            for token in database_tokens:
                if line.upper().startswith(token):
                    line = line.split('=')
                    slack_app[token] = line[1].strip()

    # Refresh the database every half hour.
    database['REFRESH_TIME'] = '1800'

    # Maximum length of a message we send.
    # Slack splits it into multiple bits when it is longer than ~4000 so this is a good limit.
    database['MAX_SENT_MESSAGE_LENGTH'] = '3500'

    with open(path_to_config, mode='w+') as configfile:
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
    write_config()
