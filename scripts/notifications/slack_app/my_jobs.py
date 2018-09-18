import os
from flask import abort, Flask, jsonify, request
# from ....scripts import job_status

app = Flask(__name__)

def is_request_valid(request):
    is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
    is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

    return is_token_valid and is_team_id_valid

@app.route('/my_jobs', methods=['POST'])
def my_jobs():
    if not is_request_valid(request):
        abort(400)

    username = request.form['text']

    try:
        from pythonlsf import lsf
        message = "We are running on summit(dev)!\n"
        on_summit = True
    except ImportError:
        message = "We are not running on summit(dev). :(\n"
        on_summit = False

    message += "Your name is " + username

    return jsonify(
        response_type='in_channel',
        text=message,
    )
