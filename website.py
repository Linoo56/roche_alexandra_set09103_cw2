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

def get_count_db(value,sql):
	db=get_db()
	sql=sql+"'"+value+"'"
	return db.cursor().execute(sql)
	
def get_count_db_simple(sql):
	db=get_db()
	return db.cursor().execute(sql)

@app.route('/')
def root():
	return render_template('home.html')

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
	prices = ['Under 1000','Over 1000']
	values = []
	sql1 = "SELECT count(*) FROM mytable WHERE Cost_per_month_in_Euro < 1000"
	sql2 = "SELECT count(*) FROM mytable WHERE Cost_per_month_in_Euro >= 1000"
	values.append([prices[0], get_count_db_simple(sql1)])
	values.append([prices[1], get_count_db_simple(sql2)])
	return render_template('pricecategories.html', prices=values)

@app.route('/schools/price/<price_range>')
def sort_prices(price_range):
	return ""

@app.route('/schools/city')
def cities():
	cities = ['Tokyo','Kyoto','Nagano','Fukuoka','Nagoya']
	values = []
	sql = "SELECT count(*) FROM mytable WHERE City="
	for city in cities:
		values.append([city, get_count_db(city,sql)])
	return render_template('citycategories.html',cities=values)

@app.route('/schools/city/<city>')
def sort_cities(city):
	return ""

@app.route('/schools/durations')
def durations():
	durations = ['Under 12 months','12 months','18 months']
	values = []
	sql1 = "SELECT count(*) FROM mytable WHERE Duration_Months < 12"
	sql2 = "SELECT count(*) FROM mytable WHERE Duration_Months = 12"
	sql3 = "SELECT count(*) FROM mytable WHERE Duration_Months = 18"
	values.append([durations[0], get_count_db_simple(sql1)])
	values.append([durations[1], get_count_db_simple(sql2)])
	values.append([durations[2], get_count_db_simple(sql3)])	
	return render_template('durationcategories.html', durations=values)

@app.route('/schools/duration/<duration>')
def sort_durations():
	return ""

if __name__ == '__main__':
	app.run(host="0.0.0.0", debug=True)
