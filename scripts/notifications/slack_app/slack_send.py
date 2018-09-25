from slackclient import SlackClient
import os


class SlackApp:
    """
    Class for sending a message via slack.
    """
    def __init__(self, bot_token):
        """
        Initialize the slack client and set the bot token.

        :param bot_token: (str) The ID for the bot.
        """
        # Set the token for the bot being used.
        # This slack bot token is hidden in the environment so it can not be stolen.
        self.bot_token = bot_token
        # Create a slack connector from the bot token
        self.client = SlackClient(self.bot_token)

    def send_message(self, channel, message):
        """
        Send a message to a slack channel.

        :param channel: (str) ID for the channel.
        :param message: (str) Message to send to the channel.
        :return:
        """
        # Attempt connection with Slack.
        if self.client.rtm_connect(with_team_state=False):
            # Call the slack api to post a message to a specific channel.
            self.client.api_call(
                "chat.postMessage",
                channel=channel,
                text=message
            )
        else:
            raise Exception("Connection failed. Exception traceback printed above.")

    def search_message(self):
        if self.client.rtm_connect(with_team_state=False):
            self.client.api_call(
                "search.messages",
                query="export"
            )
            print("I did it!")
        else:
            raise Exception("Connection failed. Exception traceback printed above.")


if __name__ == '__main__':
    # Pull the bot token from the os environment and create the connector.
    app = SlackApp(os.environ["SLACK_BOT_TOKEN"])
    app.search_message()
    # # This is the id of the channel.
    # channel = "CCRA1Q41J"
    # # Send the message to the channel.
    # app.send_message(channel=channel, message="Another test message. This time from summitdev!")
