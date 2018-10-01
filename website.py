from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/hello/<name>')
def hello(name=None):
	user = {'name':name}
	return render_template('hello.html', user=user)
