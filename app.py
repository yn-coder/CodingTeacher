import os
import flask

from flask import render_template

app = flask.Flask(__name__)

@app.route('/')
def index():
        all_files = {}
        return render_template('base.html', notebooks = all_files )

if __name__ == '__main__':
    #app.run(debug=True)
  
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)    