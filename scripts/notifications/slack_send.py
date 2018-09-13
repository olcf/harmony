from slackclient import SlackClient
import os

def send_message(message):
    # This slack bot token is hidden in the environment so it can not be stolen.
    slack_bot_token = os.environ["SLACK_BOT_TOKEN"]

    sc = SlackClient(slack_bot_token)
    if sc.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        sc.api_call(
            "chat.postMessage",
            channel="CCRA1Q41J",
            text=message
        )
    else:
        print("Connection failed. Exception traceback printed above.")


if __name__ == '__main__':
    send_message()
