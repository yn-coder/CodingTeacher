from flask import Flask, render_template, request, make_response
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
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = test_sql_url

db = SQLAlchemy(app)

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

@app.route('/')
def index():
        all_files = {}
        return render_template('index.html', notebooks = all_files )

@app.route('/help/')
def help():
        return render_template('help.html' )

@app.route('/login/<provider_name>/', methods=['GET', 'POST'])
def login(provider_name):
    """
    Login handler, must accept both GET and POST to be able to use OpenID.
    """

    # We need response object for the WerkzeugAdapter.
    response = make_response()

    # Log the user in, pass it the adapter and the provider name.
    result = authomatic.login(
        WerkzeugAdapter(
            request,
            response),
        provider_name)

    # If there is no LoginResult object, the login procedure is still pending.
    if result:
        if result.user:
            # We need to update the user to get more info.
            result.user.update()

        # The rest happens inside the template.
        return render_template('login.html', result=result)

    # Don't forget to return the response.
    return response

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

@app.route('/help/resource/<res_name>', methods=['GET'])
def help_resource(res_name):
    try:
       resp = make_response( render_template( '/resource/' + res_name + '.html' ) )
    except:
        resp = make_response("<pre>No special resource is exists!</pre>")
    # CORS
    resp.headers['Access-Control-Allow-Origin'] = '*'

    return resp

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
