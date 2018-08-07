import sys

from flask import Flask, redirect, url_for, flash, render_template
from werkzeug.contrib.fixers import ProxyFix

from flask_dance.contrib.azure import make_azure_blueprint, azure
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized, oauth_error

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = "supersekritit_now"

blueprint = make_azure_blueprint(
    client_id="e9bf7a9a-13bc-4db8-af9d-f6626ec9705f",
    client_secret="ekbvXCNU187!golTCD36[#|",
    scope=["User.Read","profile","openid","email"],
)
app.register_blueprint(blueprint, url_prefix="/login")

import os

DATABASE_URL = os.environ.get('DATABASE_URL')
test_sql_url = 'sqlite:////test.db'

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = test_sql_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)

class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

if app.config['SQLALCHEMY_DATABASE_URI'] == test_sql_url:
    db.create_all()

# setup login manager
login_manager = LoginManager()
login_manager.login_view = 'azure.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)
login_manager.init_app(app)

# https://stackoverflow.com/questions/47643448/flask-dance-cannot-get-oauth-token-without-an-associated-user
blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user, user_required=False )

# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def azure_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in with Azure.", category="error")
        return False

    resp = blueprint.session.get("/v1.0/me")
    if not resp.ok:
        msg = "Failed to fetch user info from Azure."
        flash(msg, category="error")
        return False

    azure_info = resp.json()
    azure_user_id = str(azure_info["id"])

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name,
        provider_user_id=azure_user_id,
    )
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(
            provider=blueprint.name,
            provider_user_id=azure_user_id,
            token=token,
        )

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in with Azure.")

    else:
        # Create a new local user account for this user
        user = User(
            # Remember that `email` can be None, if the user declines
            # to publish their email address on GitHub!
            email=azure_info["userPrincipalName"],
            name=azure_info["displayName"],
        )
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        login_user(user)
        flash("Successfully signed in with Azure.")

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False

@app.route("/")
def index():
    return "index"
    
    # if not azure.authorized:
        # return redirect(url_for("azure.login"))

    # try:
        # resp = azure.get("/v1.0/me")
        # assert resp.ok
        # return "You are {name} and {mail} on Azure AD".format(name=resp.json()["displayName"] ,mail=resp.json()["userPrincipalName"])
    # except (InvalidGrantError, TokenExpiredError) as e:  # or maybe any OAuth2Error
        # return redirect(url_for("azure.login"))

@app.route("/p/")
def p():
    if not azure.authorized:
        return 'not'
    else:
        return '_' + str(azure.token["expires_at"])

@app.route("/info/")
def info():
    return render_template('info.html', users = User.query.all(), oauths = OAuth.query.all() )

@app.route("/t/")
def t():
    return '0000000013'

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have logged out")
    return redirect(url_for("index"))

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
