import flask
import json
import requests
from uuid import uuid4

from datetime import datetime, timedelta
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

# Backend URLs

BE_SESSIONS = 'http://127.0.0.1:5001/api/sessions'
BE_USERS = 'http://127.0.0.1:5002/api/users'
BE_PERSONNEL = 'http://127.0.0.1:5003/api/personnel'
BE_DEPARTMENTS = 'http://127.0.0.1:5004/api/departments'

fe_port = 5000

# Default page values

page_def = 1
per_page_def = 20

app = flask.Flask(__name__)

# Session class for SessionInterface
class MySession(CallbackDict, SessionMixin):
	def __init__(self, initial = None, session_id = None, user_id = None):
		def on_update(self):
			self.modified = True
		CallbackDict.__init__(self, initial, on_update)
		self.session_id = session_id
		self.user_id = user_id
		self.modified = False
 
# SessionInterface class for Flask app
class SQLiteSessionInterface(SessionInterface):
	session_class = MySession
   
	def open_session(self, app, request):
		try:
			session_id = request.cookies.get('session_id')
			if session_id:
				serv_response = requests.get(BE_SESSIONS + '/{}'.format(session_id), params = None)
				if (serv_response.status_code == 200):
					sess_json = serv_response.json()
					if (datetime.strptime(sess_json['last_used'], '%Y-%m-%dT%H:%M:%S.%f') + timedelta(hours=1) > datetime.utcnow()):
						return self.session_class(session_id = sess_json['id'], user_id = sess_json['user_id'])
			sess_data = {'last_used': str(datetime.utcnow())}
			serv_response = requests.post(BE_SESSIONS, json = sess_data)
			if (serv_response.status_code == 201):
				sess_json = serv_response.json()
				return self.session_class(session_id = sess_json['id'], user_id = sess_json['user_id'])
		except requests.exceptions.RequestException:
			return self.session_class(session_id = str(uuid4()))
   
	def save_session(self, app, session, response):
		if session.session_id is None:
			response.set_cookie('session_id', '', expires = 0)
			return
		
		try:
			sess_data = {'user_id': session.user_id, 'last_used': str(datetime.utcnow())}
			serv_response = requests.patch(BE_SESSIONS + '/{}'.format(session.session_id), json = sess_data)
			if serv_response.status_code == 200:
				response.set_cookie('session_id', session.session_id)
		except requests.exceptions.RequestException:
			pass
	
app.session_interface = SQLiteSessionInterface()

# Error 'handling' page
def error_page(error):
	reason = {
		400: 'Bad Request',
		401: 'Unauthorized',
		403: 'Forbidden',
		404: 'Not Found',
		405: 'Method Not Allowed',
		500: 'Internal Server Error',
		503: 'Service Unavailable'
	}[error]
	
	return flask.render_template('error.html', error = {'id': error, 'reason': reason})

# Index page
@app.route('/', methods=['GET'])
def index():
	if (flask.session.user_id is None):
		return flask.redirect('/login')
	
	return flask.redirect('/me')

# User registration page
@app.route('/register', methods=['GET','POST'])
def register():
	if flask.request.method == 'GET':
		if (flask.session.user_id is not None):
			return flask.redirect('/me')
		
		return flask.render_template('registration_page.html')
	
	username = flask.request.form['username']
	firstname = flask.request.form['firstname']
	lastname = flask.request.form['lastname']
	
	email = flask.request.form['email']
	phone = flask.request.form['phone']
	password = flask.request.form['password']
	
	try:
		user_data = {'username': username, 'firstname': firstname, 'lastname': lastname, 'email': email, 'phone': phone, 'password': password}
	except requests.exceptions.RequestException:
		return error_page(503)
	
	serv_response = requests.post(BE_USERS, json = user_data)
	if (serv_response.status_code != 201):
		return error_page(serv_response.status_code)
	
	return flask.redirect('/login')

# Login page
@app.route('/login', methods=['GET','POST'])
def login():
	if flask.request.method == 'GET':
		if (flask.session.user_id is not None):
			return flask.redirect('/me')
		
		return flask.render_template('login_page.html')
	
	username = flask.request.form.get('username')
	password = flask.request.form.get('password')
	
	try:
		q = {'filters': [{'name': 'username', 'op': '==', 'val': username}], 'single': True}
		serv_response = requests.get(BE_USERS, params = {'q': json.dumps(q)})
	except requests.exceptions.RequestException:
		return error_page(503)
	
	if (serv_response.status_code != 200):
		if (serv_response.status_code == 404):
			return flask.render_template('login_page.html', error = 1)
		return error_page(serv_response.status_code)
	
	resp_data = serv_response.json()
	if (resp_data['password'] != password):
		return flask.render_template('login_page.html', username = username, error = 2)
	
	flask.session.user_id = resp_data['id']
	
	return flask.redirect('/me')

# Logout page
@app.route('/logout')
def logout():
	flask.session.user_id = None
	return flask.redirect('/')

# Personal user info page
@app.route('/me')
def user_info():
	user_id = flask.session.user_id
	if user_id is None:
		return flask.redirect('/login')
	
	try:
		serv_response = requests.get(BE_USERS + '/{}'.format(user_id), params = None)
	except requests.exceptions.RequestException:
		return error_page(503)
	
	user = serv_response.json()
	return flask.render_template('me.html', user = user)

# Personnel list page
@app.route('/personnel', methods=['GET','POST'])
def get_personnel():
	if flask.request.method == 'POST':
		return flask.redirect('/personnel/add')
	
	per_page = flask.request.args.get('per_page', per_page_def)
	page = flask.request.args.get('page', page_def)
	
	try:
		serv_response = requests.get(BE_PERSONNEL, params = {'page': page, 'results_per_page': per_page})
	except requests.exceptions.RequestException:
		return error_page(503)
	
	resp_json = serv_response.json()
	
	return flask.render_template('personnel.html', personnel = resp_json['objects'], page = int(page), per_page = int(per_page), page_count = resp_json['total_pages'])

# Input page for new employee's data
@app.route('/personnel/add', methods=['GET', 'POST'])
def post_personnel():
	if (flask.session.user_id is None):
		return flask.redirect('/login')
	
	if flask.request.method == 'GET':
		try:
			serv_response = requests.get(BE_DEPARTMENTS)
		except requests.exceptions.RequestException:
			return error_page(503)
		resp_json = serv_response.json()
		return flask.render_template('employee_add.html', departments = resp_json['objects'])

	firstname = flask.request.form.get('firstname')
	lastname = flask.request.form.get('lastname')
	hiredate = flask.request.form.get('hiredate')
	occupation = flask.request.form.get('occupation')
	
	try:
		serv_response = requests.get(BE_DEPARTMENTS + '/{}'.format(occupation), params = None)
	except requests.exceptions.RequestException:
		return error_page(503)
	
	department = serv_response.json()
	if (department is None):
		return error_page(400)
	
	try:
		serv_response = requests.post(BE_PERSONNEL, json = {'firstname': firstname, 'lastname': lastname, 'hiredate': hiredate, 'occupation': occupation})
		if (serv_response.status_code != 201):
			return error_page(serv_response.status_code)
	except requests.exceptions.RequestException:
		return error_page(503)

	return flask.redirect('/personnel')

# Existing employee's data page
# If department backend is down, occupation will be 'Unavailable'
@app.route('/personnel/<int:item_id>', methods=['GET','POST'])
def get_employee(item_id):
	if (flask.session.user_id is None):
		return flask.redirect('/login')
	
	if (flask.request.method == 'POST'):
		return delete_personnel(item_id)
	
	try:
		serv_response = requests.get(BE_PERSONNEL + '/{}'.format(item_id), params = None)
	except requests.exceptions.RequestException:
		return error_page(503)
	
	employee = serv_response.json()
	if (employee == {}):
		return error_page(404)
	
	try:
		serv_response = requests.get(BE_DEPARTMENTS + '/{}'.format(employee['occupation']), params = None)
		department = serv_response.json()
	except requests.exceptions.RequestException:
		department = {'name': 'Unavailable'}
	
	return flask.render_template('employee.html', employee = employee, department = department)

# Employee's delete request
# Delete request is used through query key 'delete': "?delete=1"
@app.route('/personnel/<int:item_id>', methods=['DELETE'])
def delete_personnel(item_id):
	if (flask.session.user_id is not None):
		try:
			serv_response = requests.delete(BE_PERSONNEL + '/{}'.format(item_id), params = None)
			if (serv_response.status_code != 200 and serv_response.status_code != 204):
				return error_page(serv_response.status_code)
		except requests.exceptions.RequestException:
			return error_page(503)
	
	return flask.redirect('/personnel')

# Department list page
@app.route('/departments', methods=['GET','POST'])
def get_departments():
	if flask.request.method == 'POST':
		return flask.redirect('/departments/add')
		
	per_page = flask.request.args.get('per_page', per_page_def)
	page = flask.request.args.get('page', page_def)
	
	try:
		serv_response = requests.get(BE_DEPARTMENTS, params = {'page': page, 'results_per_page': per_page})
	except requests.exceptions.RequestException:
		return error_page(503)
	resp_json = serv_response.json()
	
	return flask.render_template('departments.html', departments = resp_json['objects'], page = int(page), per_page = int(per_page), page_count = resp_json['total_pages'])

# Input page for new department's data
@app.route('/departments/add', methods=['GET','POST'])
def post_department():
	if (flask.session.user_id is None):
		return flask.redirect('/login')
	
	if flask.request.method == 'GET':
		return flask.render_template('department_add.html')
	
	name = flask.request.form.get('name')
	location = flask.request.form.get('location')
	email = flask.request.form.get('email')
	
	try:
		serv_response = requests.post(BE_DEPARTMENTS, json = {'name': name, 'location': location, 'email': email})
		if (serv_response.status_code != 201):
			return error_page(serv_response.status_code)
	except requests.exceptions.RequestException:
		return error_page(503)
	
	return flask.redirect('/departments')

# Existing department's data page
# If personnel backend is down, employee list will be replaced with 'Data unavailable'
@app.route('/departments/<int:class_id>', methods=['GET','POST'])
def get_department(class_id):
	if (flask.session.user_id is None):
		return flask.redirect('/login')
	
	if (flask.request.method == 'POST'):
		return delete_department(class_id)
	
	try:
		serv_response = requests.get(BE_DEPARTMENTS + '/{}'.format(class_id), params = None)
	except requests.exceptions.RequestException:
		return error_page(503)
	
	department = serv_response.json()
	if (department == {}):
		return error_page(404)
	
	try:
		q = {'filters': [{'name': 'occupation', 'op': '==', 'val': class_id}]}
		serv_response = requests.get(BE_PERSONNEL, params = {'q': json.dumps(q)})
		resp_json = serv_response.json()
	except requests.exceptions.RequestException:
		resp_json = {'objects': ''}
	
	return flask.render_template('department.html', department = department, employees = resp_json['objects'])

# Department's delete request
# Delete request is used through query key 'delete': "?delete=1"
@app.route('/departments/<int:class_id>', methods=['DELETE'])
def delete_department(class_id):
	if (flask.session.user_id is not None):
		try:
			q = {'filters': [{'name': 'occupation', 'op': '==', 'val': class_id}]}
			serv_response = requests.get(BE_PERSONNEL, params = {'q': json.dumps(q)})
			if (serv_response.status_code != 200):
				return error_page(serv_response.status_code)
			serv_json = serv_response.json()
		except requests.exceptions.RequestException:
			return error_page(503)
		
		if (serv_json['objects'] == []):
			try:
				requests.delete(BE_DEPARTMENTS + '/{}'.format(class_id), params = None)
				if (serv_response.status_code != 200 and serv_response.status_code != 204):
					return error_page(serv_response.status_code)
			except requests.exceptions.RequestException:
				return error_page(503)
				
			return flask.redirect('/departments')
	
	return error_page(405)

def main():
	app.run(port = fe_port, debug = True)

if __name__ == '__main__':
	main()