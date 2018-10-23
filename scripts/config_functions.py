import configparser
import os
import sys


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))


def write_config(file_path, password=None):
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
    database['USER'] = 'kuchta'
    if password is not None:
        database['PASSWORD'] = password
    else:
        database['PASSWORD'] = os.environ['DATABASE_PASSWORD']
    database['DATABASE_NAME'] = 'rgt'
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


def get_config(file_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))):
    conf = configparser.ConfigParser()

    conf.read(file_path)
    return conf


if __name__ == '__main__':
    if len(sys.argv) > 1:
        password = sys.argv[1]
        write_config(config_path, password)

    else:
        write_config(config_path)
