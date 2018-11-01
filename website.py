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

@app.context_processor
def utility_processor():
	def format_price(value):
		return "{:,.2f}".format(value);
	return dict(format_price=format_price)

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

@app.route('/programs/')
def listing_programs():
	db = get_db()
	sqlsch = "SELECT * FROM schools"
	schoolsData = db.cursor().execute(sqlsch)
	schools = []
	for u in schoolsData:
		schools.append(School(u[0],u[1],u[2],u[3],u[4],u[5]))
	programs = [] 
	for school in schools:
		sql="SELECT * FROM programs where schid ='"+school.schid+"'"
		programsData = db.cursor().execute(sql)
		for t in programsData:
			programs.append([school, Program(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10])])
	return render_template('programBoxes.html', programs=programs)


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

@app.route('/programs/price')
def prices():
	db = get_db()
	prices = ['U1000','O1000']
	counts = [0, 0]
	values = []
	sql = "SELECT duration, appli_fee, course_fee, acco_fee FROM programs"
	for result in db.cursor().execute(sql):
		print(result[1],result[2],result[3],result[0])
		if (result[3] != ''):
			if (result[1] != '' and ((result[1]+result[2]+result[3])/result[0])/130 < 1000):
				counts[0] = counts[0]+1
			elif (result[1] == '' and ((result[2]+result[3])/result[0])/130 < 1000):
				counts[0] = counts[0]+1
			else:
				counts[1] = counts[1]+1
			
	values.append([prices[0], counts[0]])
	values.append([prices[1], counts[1]])
	print(values)
	return render_template('pricecategories.html', prices=values)

@app.route('/programs/price/<price_range>')
def sort_prices(price_range):	
	db = get_db()
	selectedprograms = []
	programs = []
	sql="SELECT * FROM programs"
	sqlsch="SELECT * FROM schools WHERE schid='"
	programsData = db.cursor().execute(sql)
	for u in programsData:
		programs.append(Program(u[0],u[1],u[2],u[3],u[4],u[5],u[6],u[7],u[8],u[9],u[10]))
	if price_range == 'U1000':
		for program in programs:
			if program.accoFee != '' and program.appliFee != '' and ((program.appliFee+program.courseFee+program.accoFee)/program.duration)/130 < 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
			if program.accoFee != '' and program.appliFee == '' and ((program.courseFee+program.accoFee)/program.duration)/130 < 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
	elif price_range == 'O1000':
		for program in programs:
			print(program.accoFee != '', program.appliFee == '')
			if program.accoFee != '' and program.appliFee == '' and ((program.courseFee+program.accoFee)/program.duration)/130 >= 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
	
			if program.accoFee != '' and program.appliFee != '' and ((program.appliFee+program.courseFee+program.accoFee)/program.duration)/130 >= 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					print(t)
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
	else:
		abort(404) 
	print(selectedprograms)
	return render_template('sortresultsprograms.html', programs=selectedprograms)

@app.route('/schools/city')
def cities():
	cities = ['Tokyo','Kyoto','Nagano','Fukuoka','Nagoya']
	values = []
	sql = "SELECT count(*) FROM schools WHERE City="
	for city in cities:
		values.append([city, get_count_db(city,sql)])
	return render_template('citycategories.html',cities=values)

@app.route('/schools/city/<city>')
def sort_cities(city):
	db = get_db()
	schools = []
	sql="SELECT * FROM schools WHERE city='"+city+"'"
	for t in db.cursor().execute(sql):
		schools.append(School(t[0],t[1],t[2],t[3],t[4],t[5]))
	return render_template('sortresultsschools.html', schools=schools)


@app.route('/programs/duration')
def durations():
	durations = ['12months','18months','24months']
	values = []
	sql1 = "SELECT count(*) FROM programs WHERE duration = 12"
	sql2 = "SELECT count(*) FROM programs WHERE duration = 18"
	sql3 = "SELECT count(*) FROM programs WHERE duration = 24"
	values.append([durations[0], get_count_db_simple(sql1)])
	values.append([durations[1], get_count_db_simple(sql2)])
	values.append([durations[2], get_count_db_simple(sql3)])	
	return render_template('durationcategories.html', durations=values)

@app.route('/programs/duration/<duration>')
def sort_durations(duration):
	db = get_db()
	schools = []
	programs = []
	value = ''
	if duration == '12months':
		value = '=12'
	elif duration == '18months':
		value = '=18'
	elif duration == '24months':
		value = '=24'
	else:
		abort(404)
	schoolsData = db.cursor().execute("SELECT * FROM schools")
	for u in schoolsData:
		schools.append(School(u[0],u[1],u[2],u[3],u[4],u[5]))
	for school in schools:
		sql="SELECT * FROM programs WHERE duration"+value+" AND schid='"+school.schid+"'"
		programsData = db.cursor().execute(sql)
		for t in programsData:
			programs.append([school, Program(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[10])])
	return render_template('sortresultsprograms.html', programs=programs)

@app.route('/schools/search', methods=['POST'])
def search():
	value = request.form['value']
	db = get_db()
	schools = []
	sql="SELECT * FROM schools WHERE name LIKE '%"+value+"%' OR city LIKE '"+value+"' OR district LIKE '"+value+"'"
	schoolData = db.cursor().execute(sql)
	for u in schoolData:
		schools.append(School(u[0],u[1],u[2],u[3],u[4],u[5]))

	return render_template('searchresults.html', schools=schools, search=value)

@app.errorhandler(404)
def page_not_found(error):
	return "The page you requested does not exist. Sorry. We still hope you have a nice day ! :D", 404


if __name__ == '__main__':
	app.run(host="0.0.0.0", debug=True)
