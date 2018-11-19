import ConfigParser, sqlite3
import bcrypt
import mail
from functools import wraps
from school import School
from program import Program
from review import Review
from flask import Flask, request, flash, render_template, g, abort, redirect, session, url_for
app = Flask(__name__)
config = ConfigParser.ConfigParser()
config.read('etc/defaults.cfg')
app.secret_key = config.get('config','secret_key')  
db_location = 'var/sqlite3v2.db'

CURRENCIES = {
	'euro' : 130, 
	'pound' : 146, 
	'dollar' : 112
}

def requires_login(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		status = session.get('logged_in', False)
		if not status:
			return redirect(url_for('root'))
		return f(*args, **kwargs)
	return decorated
	
def requires_admin(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		status = session.get('admin', False)
		if not status:
			return redirect(url_for('root'))
		return f(*args, **kwargs)
	return decorated

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
		if value != "":
			return "{:,.2f}".format(value)
		else:
			return value
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


def init(app):
	config = ConfigParser.ConfigParser()
	try:
		config_location="etc/defaults.cfg"
		config.read(config_location)
		
		app.config['SECRET_KEY'] = config.get("config", "secret_key")
	except:
		return render_template('error.html')

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
	try:
		fav = db.cursor().execute("SELECT * FROM favorites WHERE schid=? AND user_email=?", (schid, session['user'])).fetchone()
		return render_template('description.html', school=theSchool, programs=schoolPrograms, fav=fav)
	except KeyError:
		return render_template('description.html', school=theSchool, programs=schoolPrograms)

@app.route('/schools/<schid>/submit-review', methods = ['GET','POST'])
@requires_login
def submit_review(schid):
	if request.method == 'GET':
		db = get_db()
		schdata = db.cursor().execute("SELECT * FROM schools WHERE schid = ?", [schid]).fetchone()
		school = School(schdata[0],schdata[1],schdata[2],schdata[3],schdata[4],schdata[5])
		return render_template('submitreview.html', school=school)
	else:
		db = get_db()
		score = request.form['score']
		content = request.form['review-content']
		school = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [schid]).fetchone()
		sql="INSERT INTO reviews(user_email, note, content, validated, schid) VALUES(?,?,?,?,?)"
		db.cursor().execute(sql, (session['user'], score, content, 0, schid))
		db.commit()
		userdata = db.cursor().execute("SELECT * FROM users WHERE email = ?", [session['user']]).fetchone()

		reviewid = db.cursor().execute("SELECT rowid FROM reviews WHERE user_email = ? AND schid = ?", (session['user'], schid)).fetchone()
		url = "set09103.napier.ac.uk:9176/check-review/"+str(reviewid[0])
		mail.send("Arekusandora78@gmail.com", "Review Submission", "A new review has been submited by "+session['user_name']+" ("+session['user']+") about the school "+school[0]+". Please check it out ! "+url)
		flash("Your review has been successfully sent")
		return redirect(url_for('school_description', schid=schid))

@app.route('/programs/price')
def prices():
	db = get_db()
	if session['currency'] == 'euro':
		currency = 130
	elif session['currency'] == 'pound':
		currency = 145.5
	elif session['currency'] == 'dollar':
		currency = 112
	else:
		currency = 130
	prices = ['U1000','O1000']
	counts = [0, 0]
	values = []
	sql = "SELECT duration, appli_fee, course_fee, acco_fee FROM programs"
	for result in db.cursor().execute(sql):
		if (result[3] != ''):
			if (result[1] != '' and ((result[1]+result[2]+result[3])/result[0])/currency < 1000):
				counts[0] = counts[0]+1
			elif (result[1] == '' and ((result[2]+result[3])/result[0])/currency < 1000):
				counts[0] = counts[0]+1
			else:
				counts[1] = counts[1]+1
			
	values.append([prices[0], counts[0]])
	values.append([prices[1], counts[1]])
	return render_template('pricecategories.html', prices=values)

@app.route('/programs/price/<price_range>')
def sort_prices(price_range):	
	db = get_db()
	if session['currency'] == 'euro':
		currency = 130
	elif session['currency'] == 'pound':
		currency = 145.5
	elif session['currency'] == 'dollar':
		currency = 112
	else:
		currency == 130
	selectedprograms = []
	programs = []
	sql="SELECT * FROM programs"
	sqlsch="SELECT * FROM schools WHERE schid='"
	programsData = db.cursor().execute(sql)
	for u in programsData:
		programs.append(Program(u[0],u[1],u[2],u[3],u[4],u[5],u[6],u[7],u[8],u[9],u[10]))
	if price_range == 'U1000':
		for program in programs:
			if program.accoFee != '' and program.appliFee != '' and ((program.appliFee+program.courseFee+program.accoFee)/program.duration)/currency < 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
			if program.accoFee != '' and program.appliFee == '' and ((program.courseFee+program.accoFee)/program.duration)/currency < 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
	elif price_range == 'O1000':
		for program in programs:
			if program.accoFee != '' and program.appliFee == '' and ((program.courseFee+program.accoFee)/program.duration)/currency >= 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
					selectedprograms.append([School(t[0],t[1],t[2],t[3],t[4],t[5]), program])	
	
			if program.accoFee != '' and program.appliFee != '' and ((program.appliFee+program.courseFee+program.accoFee)/program.duration)/currency >= 1000:
				school = db.cursor().execute(sqlsch+program.schId+"'")
				for t in school:
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


@app.route('/register', methods=['GET'])
def register_page():
	return render_template('registerform.html')

@app.route('/register', methods=['POST'])
def registration():
	email = request.form['inputEmail']
	password = bcrypt.hashpw(str(request.form['inputPassword']), bcrypt.gensalt())
	displayName = request.form['inputDisplayName']
	country = request.form['inputCountry']

	db = get_db()
	sql = "INSERT INTO users VALUES (?,?,?,?,?)"
	db.cursor().execute(sql, (email, password, displayName, country, 1))
	db.commit()	

	print email, password, displayName, country
	return render_template('registerform.html')

@app.route('/login', methods=['GET'])
def login_page():
	return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
	db = get_db()
	msg =""
	sql = "SELECT email, password, display_name, rank FROM users WHERE email = ?"
	email = request.form['inputEmail']
	password = request.form['inputPassword']
	user = db.cursor().execute(sql, ([email])).fetchone()
	if(user[1].encode('utf-8') == bcrypt.hashpw(password.encode('utf-8'), user[1].encode('utf-8'))):
		print "Valide"
		session['logged_in'] = True
		session['user'] = email
		session['user_name'] = user[2]
		if user[3] == 2:
			session['admin'] = True
			msg += "You are an admin"
		flash("Welcome back "+session['user_name']+" !"+msg)
		return redirect(url_for('root'))
	else:
		print "Pas valide"
		return render_template('login.html')

@app.route('/logout')
def logout():
	session.pop('user', None)
	session.pop('logged_in',None)
	session.pop('user_name', None)
	session.pop('admin', None)
	return redirect(url_for('root'))


@app.route('/profile')
@requires_login
def profile():
	db = get_db()
	reviews = []
	sql = "SELECT email, display_name, country FROM users WHERE email = ?"
	user = db.cursor().execute(sql, ([session['user']])).fetchone()
	favorites = db.cursor().execute("SELECT schid FROM favorites WHERE user_email = ? LIMIT 4", ([session['user']])).fetchall()
	reviewsData = db.cursor().execute("SELECT * FROM reviews WHERE user_email = ?", ([session['user']])).fetchall()
	for rd in reviewsData:
		theSchoolData = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [rd[6]]).fetchone()
		reviews.append([Review(rd[0],rd[1],rd[2],rd[3],rd[4],rd[5],rd[6]), theSchoolData[0]])	
	return render_template('profile.html', user=user, favorites=favorites, reviews=reviews)

@app.route('/profile/favorites')
@requires_login
def favorites():
	db = get_db()
	favschools= []
	favorites = db.cursor().execute("SELECT schid FROM favorites WHERE user_email = ?", ([session['user']])).fetchall()
	for favorite in favorites:
		print favorite
		u = db.cursor().execute("SELECT * FROM schools WHERE schid=?", favorite).fetchone()
		favschools.append(School(u[0],u[1],u[2],u[3],u[4],u[5]))
	print favschools
	return render_template('favorites.html', favorites=favschools)

@app.route('/addfav/<schid>')
@requires_login
def add_school_favorite(schid):
	db = get_db()
	sql = "INSERT INTO favorites VALUES (?,?,'')"
	school = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [schid]).fetchone()
	db.cursor().execute(sql,(session['user'], schid))
	db.commit()
	flash(school[0]+" has been added to your favorites schools")
	return redirect(request.referrer)

@app.route('/delfav/<schid>')
@requires_login
def del_school_favorite(schid):
	db = get_db()
	sql = "DELETE FROM favorites WHERE schid=? AND user_email=?"
	school = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [schid]).fetchone()
	db.cursor().execute(sql,(schid, session['user']))
	db.commit()
	flash(school[0]+" has been removed from your favorites schools")
	return redirect(request.referrer)

@app.route('/check-review/<reviewid>')
@requires_admin
def check_review(reviewid):
	db = get_db()
	reviewData = db.cursor().execute("SELECT * FROM reviews WHERE rowid = ? AND validated = 0", reviewid).fetchone()
	review = Review(reviewData[0],reviewData[1],reviewData[2],reviewData[3],reviewData[4],reviewData[5], reviewData[6])
	schoolName = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [review.schid]).fetchone()
	userName = db.cursor().execute("SELECT display_name FROM users WHERE email = ?", [review.userEmail]).fetchone()
	return render_template('reviewchecking.html', review=review, school=schoolName[0], user=userName[0])
	
				

@app.errorhandler(404)
def page_not_found(error):
	return render_template('error.html'), 404

if __name__ == '__main__':
	init(app)
	app.run(host="0.0.0.0", debug=True)
