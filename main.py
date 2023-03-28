from google.cloud import datastore
import requests

import json

from flask import request, make_response
import datetime
from os import environ as env

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from urllib.parse import quote_plus
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode
from jose import jwt
import jwt as pyjwt

from views.collections import view_collections
from views.media import view_media

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

client = datastore.Client()

LIBRARIES = "libraries"
COLLECTIONS = "collections"
MEDIA = "media"

URL = "https://portfolio-skinneem.uc.r.appspot.com"
CLIENT_ID = env.get("AUTH0_CLIENT_ID")
CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
DOMAIN = env.get("AUTH0_DOMAIN")

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

app.register_blueprint(view_collections)
app.register_blueprint(view_media)


@app.route('/')
def index():
    if 'user' not in session:
        return render_template("welcome.j2")
    else:
        payload = pyjwt.decode(session["user"], options={"verify_signature": False})
        return render_template("welcome.j2", jwt=session["user"], session=payload['name'], pretty=json.dumps(payload,
                                                                                                      indent=4))


# Retrieve a list of end-users
@app.route("/libraries", methods=['GET'])
def libraries_get():
    if request.method == 'GET':
        libraries_query = client.query(kind=LIBRARIES)
        libraries = list(libraries_query.fetch())
        return jsonify(libraries), 200
    else:
        return 'Method not recognized'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
