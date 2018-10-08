""" Web application with Azure Windows.Live OAuth and Jupyter oriented help system.
    See https://github.com/yn-coder/CodingTeacher

 """
import sys

from flask import Flask, redirect, url_for, flash, render_template, make_response, request, jsonify
from werkzeug.contrib.fixers import ProxyFix

from flask_dance.contrib.azure import make_azure_blueprint, azure
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
from flask_dance.consumer import oauth_authorized, oauth_error

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
from flask_migrate import Migrate

from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user
)

import json

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
test_sql_url = 'sqlite:///../test_ct_db1.db'

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = test_sql_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model, UserMixin):
    """User database model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    join_dt = db.Column( db.DateTime, nullable=True, default = datetime.utcnow )

class OAuth(OAuthConsumerMixin, db.Model):
    """Store authentificated users data """
    provider_user_id = db.Column(db.String(256), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    user = db.relationship(User)

class Question(db.Model):
    """Store questions and answers"""
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    dt = db.Column( db.DateTime, nullable=False, default = datetime.utcnow )
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=True)
    user = db.relationship(User)
    cell_code = db.Column(db.Text, nullable=True)
    cell_output = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return '<file_name %r>' % self.file_name

class db_log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=True)
    dt = db.Column( db.DateTime, nullable=False, default = datetime.utcnow )

def add_log_rec( arg_m ):
    l = db_log( description = arg_m )
    db.session.add(l)
    db.session.commit()

# setup login manager
login_manager = LoginManager()
login_manager.login_view = 'azure.login'

@login_manager.user_loader
def load_user(user_id):
    """Get User object by OAuth id"""
    return User.query.get(int(user_id))

db.init_app(app)
login_manager.init_app(app)

# https://stackoverflow.com/questions/47643448/flask-dance-cannot-get-oauth-token-without-an-associated-user
blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user, user_required=False )

# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def azure_logged_in(blueprint, token):
    """Login with Azure prompt"""
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
    """Site index home page"""
    return render_template('index.html' )

@app.route("/p/")
def p():
    if not azure.authorized:
        return 'not'
    else:
        return '_' + str(azure.token["expires_at"])

@app.route("/info/")
def info():
    return render_template('info.html', users = User.query.all(), oauths = OAuth.query.all(), db_log=db_log.query.all() )

@app.route('/help/')
def help():
    """Help index"""
    return render_template('help.html' )

@app.route('/users/')
def users():
    """List of users"""
    return render_template('users.html', users = User.query.all() )

# show user profile for current auth users
@app.route('/profile/')
def profile():
    """Profile page for signed user"""
    if azure.authorized:
        return render_template('profile.html' )
    else:
        flash("You are not logged.", category="error")
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    """Log out"""
    logout_user()
    flash("You have logged out")
    return redirect(url_for("index"))

@app.route('/help/q/', methods=['GET'])
def q():
    """Show list of questions"""
    return render_template('help_q.html', questions = Question.query.all() )

@app.route('/help/q/view/<q_id>/', methods=['GET'])
def q_view(q_id):
    """Show one question page"""
    return render_template('help_q_page.html', question = Question.query.get(q_id) )

def calc_answer(cell_code, cell_output, id, url_root):
    """ calculate the answer about Jupyter cell"""
    try:
        cell_output_json = json.loads(cell_output)
        if cell_output_json[0]['output_type'] == 'error':
            error_name = cell_output_json[0]['ename']
            return render_template( '/answers/python_error.html', ename = error_name, id = id, url_root = url_root )
        else:
            return 'I don''t know! May be your code is working well?'

    except:
        return 'Can''t parse the question!'

@app.route('/help/post_new_q/', methods=['POST'])
def post_new_q():
    """ API for posting new question"""
    answer = ""
    if request.method == "POST":
        # get url that the user has entered
        try:
            di = request.form.to_dict()
            cell_code = di['cell_code']
            cell_output = di['cell_output']
            nq = Question(file_name = di['file_name'], file_url = di['file_url'], description = di['description'], cell_code = cell_code, cell_output = cell_output )
            db.session.add(nq)
            db.session.commit()
            answer = calc_answer(cell_code, cell_output, nq.id, request.url_root )
            nq.answer = answer
            db.session.commit()
        except:
            print( 'error' )
            answer = 'error'

    d = { "msg" : answer }
    resp = make_response( jsonify( d ) )
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'
    print(resp)
    return resp

@app.route('/help/resource/<path:res_name>', methods=['GET']) # arg from url will redirects to template
def help_resource(res_name):
    """Show help page"""
    try:
        resp = make_response( render_template( '/resource/' + res_name.lower() + '.html', args=request.args.to_dict() ) )
    except:
        resp = make_response("<pre>No special resource is exists!</pre>")
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

# js game frame
@app.route('/help/get_game_iframe/', methods=['GET'])
def help_get_game_iframe():
    return render_template('game_iframe.html' )


if __name__ == '__main__':
    """Main Flask run routing"""
    port = int(os.environ.get('PORT', 5000))

    add_log_rec( 'restart' )

    app.run(host='0.0.0.0', port=port, debug=True)
