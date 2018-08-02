from flask import Flask, render_template, request, make_response, session,abort, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
#import json

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from config_template import CONFIG

app = Flask(__name__)
import os
DATABASE_URL = os.environ.get('DATABASE_URL')
test_sql_url = 'sqlite:////test.db'

app.secret_key = 'some secret'

if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = test_sql_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# Super quick user model with peewee
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column( db.Integer, primary_key = True )
    auth_provider = db.Column(db.String(255), nullable=False)
    auth_id = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    dt = db.Column( db.DateTime, nullable=False, default = datetime.utcnow )

    def __repr__(self):
        return '<file_name %r>' % self.file_name

if app.config['SQLALCHEMY_DATABASE_URI'] == test_sql_url:
    db.create_all()

# Instantiate Authomatic.
authomatic = Authomatic(CONFIG, 'your secret string', report_errors=False)

@login_manager.user_loader
def load_user(uid):
    try:
        return User.get(User.id == uid)
    except User.DoesNotExist:
        return None

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("choose_provider"))

@app.route('/')
def index():
    all_files = {}
    return render_template('index.html', notebooks = all_files )

@app.route('/help/')
def help():
    return render_template('help.html' )

@app.route("/login")
@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    """
    Login handler, must accept both GET and POST to be able to use OpenID.
    """

    # We need response object for the WerkzeugAdapter.
    response = make_response()

    # Log the user in, pass it the adapter and the provider name.
    result = authomatic.login(
        WerkzeugAdapter( request, response),
        provider_name,
        session=session,
        session_saver=lambda:app.save_session(session, response))

    # If there is no LoginResult object, the login procedure is still pending.
    if result:
        if result.user:
            # We need to update the user to get more info.
            result.user.update()

            # model
            #user, created = User.get_or_create(auth_provider=result.user.provider.id, auth_id=result.user.id)
            user = load_user(result.user.id)
            if user:
                pass
            else:
                user = User( auth_provider=result.user.provider.id, auth_id=result.user.id )
                db.session.add(user)
                db.session.commit()

            # flask-login
            login_user(user, remember=True)

        # The rest happens inside the template.
        return render_template('login.html', result=result)

    # Don't forget to return the response.
    return response

@app.route('/profile/')
@login_required
def profile():
    return render_template('profile.html' )

@app.route("/choose_provider")
def choose_provider():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    return redirect(url_for("login") + '/wl' )

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("choose_provider"))

@app.route('/help/q/', methods=['GET'])
def q():
    return render_template('help_q.html', questions = Question.query.all() )

@app.route('/help/post_new_q/', methods=['POST'])
def post_new_q():
    errors = []
    results = {}

    if request.method == "POST":
        # get url that the user has entered
        try:
            di = request.form.to_dict()
            nq = Question(file_name = di['file_name'], file_url = di['file_url'], description = di['description'] )
            db.session.add(nq)
            db.session.commit()
        except:
            print( 'error' )
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )

    resp = make_response("123")
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

@app.route('/help/resource/<path:res_name>', methods=['GET']) # arg from url will redirects to template
def help_resource(res_name):
    try:
       resp = make_response( render_template( '/resource/' + res_name.lower() + '.html', args=request.args.to_dict() ) )
    except:
        resp = make_response("<pre>No special resource is exists!</pre>")
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
