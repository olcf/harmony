from slackclient import SlackClient
import os
import time
import threading
from scripts.notifications.slack_app import slack_commands


class SlackApp:
    """
    Class for sending a message via slack.
    """

    # All times are in unix time.
    def __init__(self, bot_token, app_token, channel, response_time=5, max_messengers=4, verbose=0):
        """
        Construct the application.

        :param bot_token: Token for the bot in the app. This is the bot that needs to be mentioned.
        :param app_token: Token for the app.
        :param channel: Channel to check for messages from.
        :param response_time: How often to check the recent messages and send responses.
        :param max_messengers: How many messengers should be allowed to exist at once.
        :param verbose: Whether to print out what the app is currently doing. (0, 1, or 2)
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
        # Set the time when the last print occurred. This makes it easy to see how long it takes for things to occur.
        self.previous_print = time.time()
        # Set the id for the bot to find if it was mentioned.
        self.user_id = self.get_my_mention_token()

        # How often the bot should check for messages.
        self.response_time = response_time

        # Maximum number of messengers allowed.
        self.max_messengers = max_messengers

        # A list of all messenger.
        self.messenger_threads = []
        # Channel to read/send to.
        self.channel = channel

        # A message parser for when a message comes in for the app.
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
        """
        Search some list of messages and return any matches for some key.

        :param key: key to match to message text.
        :param responses: List of responses from the server that we will search.
        :return: A list of matching responses.
        """
        # Get all the messages from the list of responses after reading slack.
        # These are not the text but instead the full message packet.
        messages = []
        for response in responses:
            try:
                t = response['type']
            except KeyError:
                continue

            if t == 'message':
                messages.append(response)

        # Get all messages that contain the key.
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

    def main(self):
        """
        Run the app.

        :return:
        """

        if self.verbose:
            self.verbose_print("Trying to connect . . .")

        # Connect to the real time messaging slack API. This only needs to be connected to once and can only be
        # connected to a couple times per minute. We can do many  operations while connected.
        if self.client.rtm_connect():
            # While connected to the server do the necessary tasks.
            while self.client.server.connected:
                # Start time for checking slack.
                start = time.time()
                if self.verbose:
                    self.verbose_print("Checking for messages . . .")

                # Get all messages that mention our bot.
                recent_messages = self.get_my_mentions()
                # If the app has been mentioned, respond to it.
                if len(recent_messages) > 0:
                    if self.verbose:
                        self.verbose_print("Sending responses!")

                    # While we do not have enough room for another messenger, continue to try to remove the dead ones.
                    while len(self.messenger_threads) >= self.max_messengers:
                        if self.verbose:
                            self.verbose_print("There are " + len(self.messenger_threads) + " messengers!\n"
                                               "Too many! Waiting for one to finish.")
                        self.remove_dead_messengers()
                        time.sleep(1)

                    # Respond to all the messages.
                    self.message_responder(recent_messages)

                # Get the total time it took to take care of all tasks.
                total_time = time.time() - start
                if self.verbose == 2:
                    self.verbose_print("Finished checking in " + str(total_time) + " seconds.")
                if self.response_time - total_time > 0:
                    time.sleep(self.response_time - total_time)

    def remove_dead_messengers(self):
        """
        Remove all messengers that have completed their jobs.

        :return:
        """
        starting_size = len(self.messenger_threads)
        self.messenger_threads = [t for t in self.messenger_threads if t.isAlive()]
        if self.verbose and len(self.messenger_threads) != starting_size:
            self.verbose_print("Removed " + str(starting_size - len(self.messenger_threads)) + " dead messengers.")

    def message_responder(self, recent_messages):
        """
        Respond to some list of messages.

        :param recent_messages: A list of responses from the slack api call.
        :return:
        """
        # TODO: Instead of doing our own threading, do it through the slack api option.
        # A list of new messengers to create.
        new_messengers = []
        # For each message, create a messenger.
        for message in recent_messages:
            if self.verbose:
                self.verbose_print("Creating new messenger.")
            # Get where the message came from.
            channel = message["channel"]
            user = message["user"]

            # Try parsing the message. If an error occurs, tell the user.
            try:
                response_message = self.MP.parse_message(message, self, channel)
            except Exception as e:
                response_message = "Something went horribly horribly wrong! I got this error:\n" + \
                                   e.__class__ + "\t" + str(e)

            # Make sure to mention the user who sent the message.
            response_message = "<@" + user + "> " + response_message

            # Create the thread and add it to the new messenger list.
            thread = threading.Thread(target=self.send_message, args=(channel, response_message))
            new_messengers.append(thread)

        # Start all of the new messengers.
        for t in new_messengers:
            t.start()

        # Add the new messengers to the list of messenger.
        self.messenger_threads.extend(new_messengers)

        # Remove any completed messengers.
        self.remove_dead_messengers()

    def get_my_mentions(self):
        """
        Get all messages where our bot was mentioned.

        :return: A list of all the messages.
        """

        # Get the response from the server when we read from it. This is all the messages since the last of these calls
        # or since when we connected.
        responses = self.client.rtm_read()
        # Return all messages with our mention token.
        return self.search_messages(key=("<@" + self.user_id + ">"), responses=responses)

    def get_my_mention_token(self):
        """
        Get the token that a user mentions us at.

        :return: The token.
        """

        if self.verbose:
            self.verbose_print("Trying to get my bot token.")

        # Call the api asking for an authorization test.
        response = self.client.api_call("auth.test")
        if self.verbose:
            self.verbose_print("Found token.")
        if self.verbose == 2:
            self.verbose_print("auth.test response:")
            dic_print(response)

        # Pull the id of the caller from the auth.test.
        return response['user_id']

    def verbose_print(self, message):
        """
        Print some message verbosely meaning we also include the current time and the time since the last print.
        :param message: Message to print.
        :return:
        """

        # Rounded time since last print.
        time_since = round(time.time() - self.previous_print, 3)
        print(time.ctime() + ' [ +' + str(time_since) + '] ' + message)
        self.previous_print = time.time()


def recursive_print_dic(dic, indent=0):
    """
    Print a deeply nested set of lists, dictionaries, and variables. This is useful when looking at some response from
    the slack server.

    :param dic: Dictionary to print.
    :param indent: This should always start at 0. This is increased whenever we recursively call this to
    indent the print again.
    :return: The final formatted dictionary for printing.
    """

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
    """
    Print a dictionary nicely.

    :param dic: Dictionary to print.
    :return:
    """
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

    app.main()
