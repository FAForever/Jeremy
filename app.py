import os
import webapp
from webapp import app

# oauth bug dirty fix
os.environ['DEBUG'] = '1'

app.secret_key = os.environ['SECRET_KEY']
app.config['SESSION_TYPE'] = 'filesystem'

app_debug = 'FLASK_DEBUG' in os.environ

app.run(host="0.0.0.0", port=int(os.environ['PORT']), debug=app_debug)
