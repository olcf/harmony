from slackclient import SlackClient
import os
import flask

class SlackApp:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.client = SlackClient(self.bot_token)

    def send_message(self, channel, message):
        # This slack bot token is hidden in the environment so it can not be stolen.
        if self.client.rtm_connect(with_team_state=False):
            print("Starter Bot connected and running!")
            self.client.api_call(
                "chat.postMessage",
                channel=channel,
                text=message
            )
        else:
            print("Connection failed. Exception traceback printed above.")


if __name__ == '__main__':
    app = SlackApp(os.environ["SLACK_BOT_TOKEN"])
    channel = "CCRA1Q41J"
    app.send_message(channel=channel, message="Another test message. This time from summitdev!")
