from slackclient import SlackClient
import os
import time


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

    def search_messages(self, message):
        start = time.time()
        if self.client.rtm_connect(with_team_state=False):
            response = self.client.api_call(
                "search.messages",
                query=message,
                sort='timestamp'
            )
        else:
            raise Exception("Connection failed. Exception traceback printed above.")

        if not response['ok']:
            raise Exception(str(response))

        print(time.time() - start)
        # Print response
        print(print_dic(response))

        print("Number of messages:",len(response['messages']['matches']))

        return response

    def get_time_stamp(self, response_message):
        exit()

def print_dic(dic, indent=0):
    message = ""
    tab = "    "
    new_line = '\n'
    if type(dic) is dict:
        for key in dic.keys():
            message += new_line + indent*tab + "'" + key + "': {" + print_dic(dic[key], indent=indent+1) + "}" + new_line + indent*tab
    elif type(dic) is list:
        for element in dic:
            message += new_line + indent*tab + "[" + print_dic(element, indent=indent+1) + "]" + new_line + indent*tab
    else:
        message += tab + str(dic) + tab
        message = message.encode('ascii', 'replace')
        message = message.decode('ascii')
    return message

# Only respond to messages if they are somewhat recent. How to look for mentions? Reduce the number of 'responses' since duplicated.

if __name__ == '__main__':
    # Pull the bot token from the os environment and create the connector.
    app = SlackApp(os.environ["SLACK_USER_TOKEN"])
    app.search_messages("example_example_example_example_example")
    # # This is the id of the channel.
    # channel = "CCRA1Q41J"
    # # Send the message to the channel.
    # app.send_message(channel=channel, message="BWAHAHAHHAHAHAHAHA!!!!! The computer has taken Cameron's account!!! The slack client needs user permissions and thus needs it's own account.")
