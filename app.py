from flask import Flask, redirect, url_for
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.contrib.azure import make_azure_blueprint, azure

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = "supersekrit"
blueprint = make_azure_blueprint(
    client_id="e9bf7a9a-13bc-4db8-af9d-f6626ec9705f",
    client_secret="ekbvXCNU187!golTCD36[#|",
    scope=["User.Read","profile","openid","email"]
)
app.register_blueprint(blueprint, url_prefix="/login")

@app.route("/")
def index():
    if not azure.authorized:
        return redirect(url_for("azure.login"))

    resp = azure.get("/v1.0/me")
    assert resp.ok
    print(resp.json())
    return "You are {name} and {mail} on Azure AD".format(name=resp.json()["displayName"] ,mail=resp.json()["userPrincipalName"])

@app.route("/p/")
def p():
    if not azure.authorized:
        return 'not'
    else:
        return '_' + azure.token["expires_at"]

@app.route("/t/")
def t():
    return '0000000002'

if __name__ == '__main__':

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
