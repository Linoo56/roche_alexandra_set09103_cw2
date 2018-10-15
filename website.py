import ConfigParser, sqlite3
from flask import Flask, request, render_template, g
app = Flask(__name__)
db_location = 'var/sqlite3.db'

def get_db():
	db = getattr(g,'db', None)
	if db is None:
		db = sqlite3.connect(db_location)
		g.db = db
	return db

@app.teardown_appcontext
def close_db_connection(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

def init_db():
	

@app.route('/')
def root():
	return "Hello Napier from the configuration testing app"


if __name__ == '__main__':
	init(app)
	app.run(
	host =app.config['ip_address'],
	port =int(app.config ['port']))
