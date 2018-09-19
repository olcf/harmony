import os
from flask import abort, Flask, jsonify, request
# from ....scripts import job_status

# Create the flask app
app = Flask(__name__)


# Test if an incoming Slack request is valid.
def is_request_valid(request):
    # Compare tokens
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    # Compare team ids
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid


# If the app points to a URL that ends with '/my_jobs' then run this.
# 'POST' means that this will send a message.
@app.route('/my_jobs', methods=['POST'])
def my_jobs():
    # If invalid request then it will abort with a 400 error.
    if not is_request_valid(request):
        abort(400)

    # Get the text from the request. This is the username of the asker.
    username = request.form['text']

    # Test is on summit(dev) or not. This will also work on any machine setup with pythonlsf.
    try:
        from pythonlsf import lsf
        message = "We are running on summit(dev)!\n"
        on_summit = True
    except ImportError:
        message = "We are not running on summit(dev). :(\n"
        on_summit = False

    message += "Your name is " + username

    # Return a json with the type of response and the text to return. There are many possible jsons that can be returned.
    return jsonify(
        response_type='in_channel',
        text=message,
    )
