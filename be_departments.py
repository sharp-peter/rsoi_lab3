from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_restless

be_port = 5004
db_path = 'sqlite:///server_database.db'

# Backend for departments
# Departments table is located in on-disk database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
sql_db = SQLAlchemy(app)

class Department(sql_db.Model):
    __tablename__ = 'departments'
    id = sql_db.Column(sql_db.Integer, primary_key=True)
    name = sql_db.Column(sql_db.Unicode, nullable=False, unique=True)
    location = sql_db.Column(sql_db.Unicode, nullable=False)
    email = sql_db.Column(sql_db.Unicode, nullable=False, unique=True)

sql_db.create_all()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db = sql_db)
manager.create_api(Department, collection_name='departments', methods=['GET','POST','PUT','DELETE'])

app.run(port = be_port, debug = True)