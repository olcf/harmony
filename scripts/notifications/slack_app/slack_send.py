from slackclient import SlackClient
import os
import time
import threading
from scripts.notifications.slack_app import slack_commands
import sys


class SlackApp:
    """
    Class for sending a message via slack.
    """

    # All times are in unix time.
    def __init__(self, bot_token, app_token, channel, response_time=5, max_messengers=4, verbose=0):
        """
        Initialize the slack client and set the bot token.

        :param bot_token: (str) The ID for the bot.
        :param verbose: (bool) Whether to print current activity.
        """
        # Set the token for the bot being used.
        # This slack bot token is hidden in the environment so it can not be stolen.
        self.bot_token = bot_token
        # Same with the user token.
        self.app_token = app_token
        # Create a slack connector from the bot token
        self.client = SlackClient(self.bot_token)
        # Set the verbosity
        self.verbose = verbose
        self.previous_print = time.time()
        # Set the id for the bot to find if it was mentioned.
        self.user_id = self.get_my_mention_token()

        # How often the bot should check for messages.
        self.response_time = response_time

        self.max_messengers = max_messengers

        self.messenger_threads = []
        self.channel = channel

        self.MP = slack_commands.MessageParser()

    def send_message(self, channel, message):
        """
        Send a message to a slack channel.

        :param channel: (str) ID for the channel.
        :param message: (str) Message to send to the channel.
        :return:
        """
        # Call the slack api to post a message to a specific channel.
        start = time.time()
        self.client.rtm_send_message(channel, message)
        if self.verbose:
            self.verbose_print("Sent message in " + str(time.time() - start) + " seconds.")
        return

    def search_messages(self, key, responses):
        # Get all the messages from the list of responses when reading slack.
        messages = []
        for response in responses:
            try:
                t = response['type']
            except KeyError:
                continue

            if t == 'message':
                messages.append(response)

        matching_messages = []
        for message in messages:
            if key in message['text']:
                matching_messages.append(message)

        if self.verbose:
            self.verbose_print('[' + str(len(matching_messages)) + '/' + str(len(messages)) + ']' + ' matching messages.')

        if self.verbose == 2:
            # Print response
            dic_print(responses)

            if len(responses) == 0:
                self.verbose_print("Number of responses searched:" + str(len(responses))
                                   + " (i.e. No responses in the channel in the past "
                                   + str(self.response_time) + " seconds)")
            else:
                self.verbose_print("Number of responses searched:" + str(len(responses)))
            self.verbose_print("Number of matching messages:" + str(len(matching_messages)))

        return matching_messages

    def respond(self):
        if self.verbose:
            self.verbose_print("Trying to connect . . .")
        if self.client.rtm_connect():
            while self.client.server.connected:
                start = time.time()
                if self.verbose:
                    self.verbose_print("Checking for messages . . .")

                recent_messages = self.get_my_mentions()
                if len(recent_messages) > 0:
                    if self.verbose:
                        self.verbose_print("Sending responses!")

                    while len(self.messenger_threads) >= self.max_messengers:
                        if self.verbose:
                            self.verbose_print("There are " + len(self.messenger_threads) + " messengers!\n"
                                               "Too many! Waiting for one to finish.")
                        self.remove_dead_messengers()
                        time.sleep(1)

                    self.message_responder(recent_messages)

                total_time = time.time() - start
                if self.verbose == 2:
                    self.verbose_print("Finished checking in " + str(total_time) + " seconds.")
                if self.response_time - total_time > 0:
                    time.sleep(self.response_time - total_time)

    def remove_dead_messengers(self):
        starting_size = len(self.messenger_threads)
        self.messenger_threads = [t for t in self.messenger_threads if not t.isAlive()]
        if self.verbose and len(self.messenger_threads) != starting_size:
            self.verbose_print("Removed " + str(starting_size - len(self.messenger_threads)) + " dead messengers.")

    def message_responder(self, recent_messages):
        new_messengers = []
        for message in recent_messages:
            if self.verbose:
                self.verbose_print("Creating new messenger.")
            channel = message["channel"]
            user = message["user"]

            # response_message = "Hi <@" + user + ">! I can respond! I hope to have new features soon!"
            try:
                response_message = self.MP.parse_message(message['text'])
            except Exception as e:
                print("An error occurred! Here is the traceback:\n" + \
                      str(sys.exc_info()[2]))
                response_message = "Something went horribly horribly wrong! I got this error:\n" + \
                                   str(e.__class__) + "\t" + str(e)

            thread = threading.Thread(target=self.send_message, args=(channel, response_message))
            thread.daemon = True
            new_messengers.append(thread)
        for t in new_messengers:
            t.start()
        self.messenger_threads.extend(new_messengers)

        self.remove_dead_messengers()

    def get_my_mentions(self):
        responses = self.client.rtm_read()
        return self.search_messages(key=("<@" + self.user_id + ">"), responses=responses)

    def get_my_mention_token(self):
        if self.verbose:
            self.verbose_print("Trying to get my bot token.")

        response = self.client.api_call("auth.test")
        if self.verbose:
            self.verbose_print("Found token.")
        if self.verbose == 2:
            self.verbose_print("auth.test response:")
            dic_print(response)

        return response['user_id']

    def verbose_print(self, message):
        time_since = round(time.time() - self.previous_print, 3)
        print(time.ctime() + ' [ +' + str(time_since) + '] ' + message)
        self.previous_print = time.time()


def recursive_print_dic(dic, indent=0):
    message = ""
    tab = "    "
    new_line = '\n'
    if type(dic) is dict:
        for key in dic.keys():
            message += new_line + indent * tab + "'" + key + "': {" + recursive_print_dic(dic[key],
                                                                                          indent=indent + 1) + "}" + new_line + indent * tab
    elif type(dic) is list:
        for element in dic:
            message += new_line + indent * tab + "[" + recursive_print_dic(element,
                                                                           indent=indent + 1) + "]" + new_line + indent * tab
    else:
        message += tab + str(dic) + tab
        message = message.encode('ascii', 'replace')
        message = message.decode('ascii')
    return message


def dic_print(dic):
    m = recursive_print_dic(dic)
    print(m)


# Only respond to messages if they are somewhat recent.
# How to look for mentions? Reduce the number of 'responses' since duplicated.

if __name__ == '__main__':
    bot_token = os.environ["SLACK_BOT_TOKEN"]
    app_token = os.environ["SLACK_APP_TOKEN"]
    # This is the id of the channel.
    # TODO: Set this as environment variable.
    channel = "CCRA1Q41J"
    # Pull the bot token from the os environment and create the connector.
    app = SlackApp(bot_token=bot_token, app_token=app_token, channel=channel, response_time=1, verbose=1)

    app.respond()
