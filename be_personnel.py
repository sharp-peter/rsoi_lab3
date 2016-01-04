from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_restless

be_port = 5003
db_path = 'sqlite:///server_database.db'

# Backend for personnel
# Personnel table is located in on-disk database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
sql_db = SQLAlchemy(app)

class Employee(sql_db.Model):
	__tablename__ = 'personnel'
	id = sql_db.Column(sql_db.Integer, primary_key=True)
	firstname = sql_db.Column(sql_db.Unicode, nullable=False)
	lastname = sql_db.Column(sql_db.Unicode, nullable=False)
	hiredate = sql_db.Column(sql_db.Date, nullable=False)
	occupation = sql_db.Column(sql_db.Integer, nullable=False)

sql_db.create_all()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db = sql_db)
manager.create_api(Employee, collection_name='personnel', methods=['GET','POST','PUT','DELETE'])

app.run(port = be_port, debug = True)