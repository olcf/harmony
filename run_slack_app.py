from scripts.notifications.slack_app import slack_application
from scripts import config_functions


def run():
    """
    Run the slack application.
    """
    # Get the config.
    config = config_functions.get_config()
    slack_config = config['SLACK_APP']
    # Get all necessary variables from the config.
    bot_token = slack_config["slack_bot_token"]
    app_token = slack_config["slack_app_token"]
    # This is the id of the channel.
    channel = slack_config["slack_harmony_channel"]
    # How often the bot should recheck the channel.
    watch_time = float(slack_config["watch_time"])
    # Maximum number of message senders.
    max_messengers = int(slack_config["max_messengers"])
    # Maximum number of reads from slack when pulling messages.
    max_reads = int(slack_config["max_reads"])
    # Maximum message length to try to read.
    max_message_length = int(slack_config["max_message_length"])
    # Maximum number of keys allowed in any message from slack.
    max_message_keys = int(slack_config["max_message_keys"])
    max_sent_message_length = int(slack_config["max_sent_message_length"])

    # Pull the bot token from the os environment and create the connector.
    app = slack_application.SlackApp(bot_token=bot_token, app_token=app_token, channel=channel, watch_time=watch_time,
                                     verbose=1, max_messengers=max_messengers, max_reads=max_reads,
                                     max_message_length=max_message_length, max_message_keys=max_message_keys,
                                     max_sent_message_length=max_sent_message_length)

    app.main()


if __name__ == '__main__':
    run()
