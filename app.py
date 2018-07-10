from flask import Flask, render_template, request, make_response
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic

from config_template import CONFIG

app = Flask(__name__)

# Instantiate Authomatic.
authomatic = Authomatic(CONFIG, 'your secret string', report_errors=False)

@app.route('/')
def index():
        all_files = {}
        response = make_response()

        result = authomatic.login(
            WerkzeugAdapter(
                request,
                response),
            'wl')

        # If there is no LoginResult object, the login procedure is still pending.
        if result:
            if result.user:
                # We need to update the user to get more info.
                result.user.update()

        return render_template('index.html', notebooks = all_files, u = result )

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

if __name__ == '__main__':
    #app.run(debug=True)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)