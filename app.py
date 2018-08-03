from flask import Flask, redirect, url_for
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.contrib.azure import make_azure_blueprint, azure

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = "supersekrit"
blueprint = make_azure_blueprint(
    client_id="e9bf7a9a-13bc-4db8-af9d-f6626ec9705f",
    client_secret="ekbvXCNU187!golTCD36[#|",
)
app.register_blueprint(blueprint, url_prefix="/login")

@app.route("/")
def index():
    if not azure.authorized:
        return redirect(url_for("azure.login"))
    resp = azure.get("/user")
    assert resp.ok
    return "You are @{login} on Azure".format(login=resp.json()["login"])

@app.route("/t/")
def t():
    return '123'
    
if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
