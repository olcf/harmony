from slackclient import SlackClient
import os
import time
import threading
from scripts.notifications.slack_app import slack_commands
import sys
import re
from scripts import config_functions
import math
import copy


class SlackApp:
    """
    Class for sending a message via slack.
    """

    # All times are in unix time.
    def __init__(self, bot_token, app_token, channel, watch_time=5, max_messengers=4, verbose=0, max_reads=100,
                 max_message_length=100, max_message_keys=20):
        """
        Construct the application.

        :param bot_token: Token for the bot in the app. This is the bot that needs to be mentioned.
        :param app_token: Token for the app.
        :param channel: Channel to check for messages from.
        :param watch_time: How often to check the recent messages and send responses.
        :param max_messengers: How many messengers should be allowed to exist at once.
        :param verbose: Whether to print out what the app is currently doing. (0, 1, or 2)
        :param max_reads: How many responses from slack to go through each time we loop.
        :param max_message_length: Maximum length of a message that we try to parse.
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
        self.watch_time = watch_time

        # Maximum number of messengers allowed.
        self.max_messengers = max_messengers

        # A list of all messenger.
        self.messenger_threads = []
        # Channel to read/send to.
        self.channel = channel

        # A message parser for when a message comes in for the app.
        self.MP = slack_commands.MessageParser()

        # Only read a certain number of responses from the server. This prevents an overflow of messages from coming in.
        self.max_reads = max_reads

        # Only read messages less than some length.
        self.max_message_length = max_message_length

        # Only look at messages with less than this number of keys.
        self.max_message_keys = max_message_keys

        # Slack splits messages if they are too long so we set a limit where we want to split it.
        self.max_sent_message_length = max_sent_message_length

    def send_message(self, channel, message):
        """
        Send a message to a slack channel.

        :param channel: (str) ID for the channel.
        :param message: (str) Message to send to the channel.
        :return:
        """
        # Call the slack api to post a message to a specific channel.
        start = time.time()
        split_message = self.split_message_to_send(message)
        for i in range(len(split_message)):
            message = split_message[i]
            if self.verbose == 2:
                self.verbose_print("Sending message part.\n" + message)
            self.client.rtm_send_message(channel, message)

        if self.verbose:
            self.verbose_print("Sent message in " + str(time.time() - start) + " seconds.")
        return

    def split_message_to_send(self, message):
        """
        Split a message that is too long to send as a single message to slack.

        :param message: Message to split.
        :return: A list containing the split message parts.
        """
        # If the message does not need to be split, just return it as a list.
        if len(message) <= self.max_sent_message_length:
            return [message]

        if self.verbose:
            self.verbose_print("Splitting long message.")

        # Find the number of different pieces the message will be split into.
        num_parts = math.ceil(float(len(message)) / self.max_sent_message_length)
        # Get the length of each split to try to split evenly.
        split_length = int(len(message) / num_parts)
        # TODO: Split on '\n' if available.

        # Copy the message so the original is not changed.
        changed_message = copy.copy(message)
        # Set the index of the current split.
        index = split_length
        # Set the length of the new split if we are splitting in a place where formatting is needed.
        new_split_length = None
        # Create list for holding split message.
        split_message = []
        # While we have not yet hit the end, continue.
        while index < len(message):
            # Count the number of occurences of the string that implies formatting.
            before_count = message[:index].count('```')
            after_count = message[index:].count('```')

            if before_count % 2 != 0 and after_count != 0:
                if new_split_length is None:
                    message_part = changed_message[0:split_length] + '```'
                    changed_message = '```' + changed_message[split_length:]
                    new_split_length = split_length + 3
                else:
                    message_part = changed_message[0:new_split_length] + '```'
                    changed_message = '```' + changed_message[new_split_length]
            else:
                new_split_length = None
                message_part = changed_message[0:split_length]
                changed_message = changed_message[split_length:]

            split_message.append(message_part)
            index += split_length

        split_message.append(changed_message)

        return split_message

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
            if len(responses) == 0:
                self.verbose_print("Number of responses searched:" + str(len(responses))
                                   + " (i.e. No responses in the channel in the past "
                                   + str(self.watch_time) + " seconds)")
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
                if self.watch_time - total_time > 0:
                    time.sleep(self.watch_time - total_time)

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

        # TODO: Check if the response from the server was ok.

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
                print("An error occurred! Here is the traceback:\n" + \
                      str(sys.exc_info()[2]))
                response_message = "Something went horribly horribly wrong! I got this error:\n" + \
                                   str(e.__class__) + "\t" + str(e)

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

        # rtm_read only gets a single frame from the slack client.
        # It can fall behind if there are frames not yet read which is why we do the following iteration stuff.

        # Get the response from the server when we read from it. This is all the messages since the last of these calls
        # or since when we connected.
        responses = []
        # Read the first response.
        response = self.client.rtm_read()
        # Count the number of times we have iterated.
        iterations = 0
        # While we are still getting new responses and we have not iterated the maximum number of times.
        while len(response) != 0 and iterations < self.max_reads:
            # Increment iterations.
            iterations += 1
            # For each message in the response (it is always one but this is just to be safe)
            for message in response:
                # If message was ok then add it to the list of messages we will respond to.
                if self.allowable_mention(message):
                    self.verbose_print("Message was allowable:\n" + str(message))
                    responses.append(message)
                # Otherwise do not.
                else:
                    self.verbose_print("Message was not allowable:\n" + str(message))

            if iterations < self.max_reads - 1:
                response = self.client.rtm_read()

        # Return all messages with our mention token.
        return self.search_messages(key=("<@" + self.user_id + ">"), responses=responses)

    def allowable_mention(self, message):
        """
        Check if some message in the channel is usable or should be ignored.

        :param message: Message from rtm_read.
        :return: Whether the message was deemed suitable.
        """
        def match(string, search=re.compile(r'[^a-z0-9<>@_ ]', re.IGNORECASE).search):
            """
            Test if a string only contains certain characters. This is nice and safe since it is a simple regex.
            :param string: The string to search.
            :param search: The regex search.
            :return: Whether the string only contained those characters.
            """
            return not bool(search(string))

        # Try the following code. If it does not work and a key error is the issue then show the server runner.
        try:
            # Check that the message has a reasonable amount of text for us to parse.
            if len(message['text']) > self.max_message_length:
                if self.verbose:
                    self.verbose_print("This message had too much text.\n" + str(message))
                return False

            # Check that the text of the message only contains alphanumerics
            # and '<', '>', and '@' so that our user can be mentioned.
            # We do this first so that future error messages can be shown with less string parsing danger.
            if not match(message['text']):
                if self.verbose:
                    self.verbose_print("This message had weird text that I could not understand.")
                return False

            # Check that there is not an enormous excess of keys.
            if len(message.keys()) > self.max_message_keys:
                if self.verbose:
                    self.verbose_print("This message had too many keys.\n" + str(message))
                return False

            # Check that the message and event are less than 10 * response time old.
            message_age = time.time() - float(message['ts'])
            event_age = time.time() - float(message['event_ts'])

            if message_age > self.watch_time * 10:
                if self.verbose:
                    self.verbose_print("This message was too old.\n" + str(message))
                return False
            if event_age > self.watch_time * 10:
                if self.verbose:
                    self.verbose_print("The event that corresponds to this message was too old.\n" + str(message))
                return False

            # Test if correct channel. Only read until end of channel length and no more.
            if self.channel != message['channel'][:len(channel)]:
                if self.verbose:
                    self.verbose_print("The channel that corresponds to this message was not the channel this"
                                       " bot was meant for.\n" + str(message))

        except KeyError as e:
            # One of those many keys did not exist.
            if self.verbose:
                self.verbose_print("This message did not have the " + str(e) + " key.")
            return False

        # If it passes all tests then it is ok to parse.
        return True

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
            message += new_line + indent * tab + "'" + key + "': {" + \
                       recursive_print_dic(dic[key], indent=indent + 1) + "}" + new_line + indent * tab
    elif type(dic) is list:
        for element in dic:
            message += new_line + indent * tab + "[" + \
                       recursive_print_dic(element, indent=indent + 1) + "]" + new_line + indent * tab
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


if __name__ == '__main__':
    config = config_functions.get_config()
    slack_config = config['SLACK_APP']
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

    # Pull the bot token from the os environment and create the connector.
    app = SlackApp(bot_token=bot_token, app_token=app_token, channel=channel, watch_time=watch_time,
                   verbose=1, max_messengers=max_messengers, max_reads=max_reads, max_message_length=max_message_length,
                   max_message_keys=max_message_keys)

    app.main()
