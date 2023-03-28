from main import request, requests, session, redirect, url_for, urlencode
from main import CLIENT_ID, CLIENT_SECRET, DOMAIN
from main import oauth, pyjwt, app, datastore, env, quote_plus

client = datastore.Client()
LIBRARIES = "libraries"
COLLECTIONS = "collections"
MEDIA = "media"

# Generate a JWT from the Auth0 domain and return it
# Request: JSON body with 2 properties with "username" and "password"
#       of a user registered with this Auth0 domain
# Response: JSON with the JWT as the value of the property id_token
@app.route('/login', methods=['GET','POST'])
def login_user():
    username = request.form.get("username")
    password = request.form.get("password")
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    try:
        # Login the user
        r = requests.post(url, json=body, headers=headers)
        session["user"] = r.json()["id_token"]
        redirect("/")
        return r.text, 200, {"Content-Type": "application/json"}
    except:
        return "\n'Error': 'Invalid username/password.'\n"

@app.route("/signup", methods=['GET','POST'])
def signup():
    if not request.form["name"] or not request.form["type"] or not request.form["capacity"]:
        return "\n'Error': 'Invalid entries to create a user.'\n", 400

    content = request.form

    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True, name=content.get("name"),
                             type=content.get("type"), capacity=content.get("capacity"))
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token["id_token"]

    content = request.args
    payload = pyjwt.decode(session["user"], options={"verify_signature": False})
    # Create the user when signing up
    new_library = datastore.entity.Entity(key=client.key(LIBRARIES))
    new_library.update(
        {"id": payload["sub"], "name": content["name"], "type": content["type"],
         "capacity": content["capacity"]}
        )
    client.put(new_library)
    redirect("/")
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
