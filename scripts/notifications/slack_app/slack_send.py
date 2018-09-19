from slackclient import SlackClient
import os
import flask


# Class for sending a message whenever called.
class SlackApp:
    def __init__(self, bot_token):
        # Set the token for the bot being used.
        # This slack bot token is hidden in the environment so it can not be stolen.
        self.bot_token = bot_token
        # Create a slack connector from the bot token
        self.client = SlackClient(self.bot_token)

    # Send a message to a specific channel.
    def send_message(self, channel, message):
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


if __name__ == '__main__':
    # Pull the bot token from the os environment and create the connector.
    app = SlackApp(os.environ["SLACK_BOT_TOKEN"])
    # This is the id of the channel.
    channel = "CCRA1Q41J"
    # Send the message to the channel.
    app.send_message(channel=channel, message="Another test message. This time from summitdev!")
