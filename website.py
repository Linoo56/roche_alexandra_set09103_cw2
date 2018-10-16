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
	with app.app_context():
		db = get_db()
		with app.open_ressource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

@app.route('/')
def root():
	return ""

@app.route('/schools/')
def listing_schools():
	db = get_db()
	sql="SELECT * FROM mytable"
	return render_template('boxes.html', schools=db.cursor().execute(sql))

@app.route('/schools/<number>')	
def school_description(number):
	db = get_db()
	sql="SELECT * FROM mytable WHERE Number=%s" % number
	return render_template('description.html', schools=db.cursor().execute(sql))

@app.route('/schools/price')
def prices():
	return ""

@app.route('/schools/price/<price_range>')
def short_prices():
	return ""

@app.route('/schools/city')
def cities():
	return ""

@app.route('/schools/city/<city>')
def short_cities():
	return ""

@app.route('/schools/accomodation')
def accomodations():
	return ""

@app.route('/schools/accomodation/<type>')
def short_accomodation():
	return ""

if __name__ == '__main__':
	app.run(host="0.0.0.0", debug=True)
