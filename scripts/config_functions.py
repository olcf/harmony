import configparser
import os


def write_config(file_path):
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
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))
    write_config(config_path)
