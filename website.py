from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def root():
	return "The default route"

@app.route("/account/", methods=['GET','POST'])
def account():
	if request.method == 'POST':
		print request.form
		name = request.form['name']
		return "Hello %s" % name
	else:
		page='''
		<html><body>
			<form action="" method="post" name="form">
				<label for="name">Name:</label>
				<input type="text" name="name" id="name"/>
				<input type="submit" name="submit" id="submit"/>
			</form>
		</body><html>'''
		return page
