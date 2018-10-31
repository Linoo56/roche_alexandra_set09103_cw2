import ConfigParser, sqlite3
from school import School
from program import Program
from flask import Flask, request, render_template, g, abort
app = Flask(__name__)
db_location = 'var/sqlite3v2.db'

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
	sql="SELECT * FROM schools"
	schoolsData = db.cursor().execute(sql)
	schools = [] 
	for t in schoolsData:
		schools.append(School(t[0],t[1],t[2],t[3],t[4],t[5]))
	return render_template('boxes.html', schools=schools)

@app.route('/schools/<schid>')	
def school_description(schid):
	db = get_db()
	sqlSch="SELECT * FROM schools WHERE schid='"+schid+"'"
	sqlPro="SELECT * FROM programs WHERE schid='"+schid+"'"
	schoolData = db.cursor().execute(sqlSch)
	programsData = db.cursor().execute(sqlPro)
	schoolPrograms = []
	for t in schoolData:
		theSchool = School(t[0],t[1],t[2],t[3],t[4],t[5])
	for u in programsData:
		schoolPrograms.append(Program(u[0],u[1],u[2],u[3],u[4],u[5],u[6],u[7],u[8],u[9],u[10]))
	return render_template('description.html', school=theSchool, programs=schoolPrograms)

@app.route('/schools/price')
def prices():
	prices = ['U1000','O1000']
	values = []
	sql1 = "SELECT count(*) FROM mytable WHERE Cost_per_month_in_Euro < 1000"
	sql2 = "SELECT count(*) FROM mytable WHERE Cost_per_month_in_Euro >= 1000"
	values.append([prices[0], get_count_db_simple(sql1)])
	values.append([prices[1], get_count_db_simple(sql2)])
	return render_template('pricecategories.html', prices=values)

@app.route('/schools/price/<price_range>')
def sort_prices(price_range):	
	db = get_db()
	value = ''
	if price_range == 'U1000':
		value = '<1000'
	elif price_range == 'O1000':
		value = '>=1000'
	else:
		abort(404) 
	sql="SELECT * FROM mytable WHERE Cost_per_month_in_Euro"+value+""
	return render_template('sortresults.html', schools=db.cursor().execute(sql))

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
	db = get_db()
	sql="SELECT * FROM mytable WHERE City='"+city+"'"
	return render_template('sortresults.html', schools=db.cursor().execute(sql))


@app.route('/schools/durations')
def durations():
	durations = ['U12months','12months','18months']
	values = []
	sql1 = "SELECT count(*) FROM mytable WHERE Duration_Months < 12"
	sql2 = "SELECT count(*) FROM mytable WHERE Duration_Months = 12"
	sql3 = "SELECT count(*) FROM mytable WHERE Duration_Months = 18"
	values.append([durations[0], get_count_db_simple(sql1)])
	values.append([durations[1], get_count_db_simple(sql2)])
	values.append([durations[2], get_count_db_simple(sql3)])	
	return render_template('durationcategories.html', durations=values)

@app.route('/schools/duration/<duration>')
def sort_durations(duration):
	db = get_db()
	value = ''
	if duration == 'U12months':
		value = '<12'
	elif duration == '12months':
		value = '=12'
	elif duration == '18months':
		value = '=18'
	else:
		abort(404)
	sql="SELECT * FROM mytable WHERE Duration_Months"+value+""
	return render_template('sortresults.html', schools=db.cursor().execute(sql))

@app.route('/schools/search', methods=['POST'])
def search():
	value = request.form['value']
	db = get_db()
	sql="SELECT * FROM mytable WHERE Name LIKE '%"+value+"%' OR City LIKE '"+value+"' OR District LIKE '"+value+"'"
	return render_template('searchresults.html', schools=db.cursor().execute(sql), search=value)

@app.errorhandler(404)
def page_not_found(error):
	return "The page you requested does not exist. Sorry. We still hope you have a nice day ! :D", 404


if __name__ == '__main__':
	app.run(host="0.0.0.0", debug=True)
