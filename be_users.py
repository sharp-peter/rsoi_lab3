from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_restless

be_port = 5002
db_path = 'sqlite:///server_database.db'

# Backend for users
# Users table is located in on-disk database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
sql_db = SQLAlchemy(app)

class User(sql_db.Model):
    __tablename__ = 'users'
    id = sql_db.Column(sql_db.Integer, primary_key=True)
    username = sql_db.Column(sql_db.Unicode, nullable=False)
    firstname = sql_db.Column(sql_db.Unicode, nullable=False)
    lastname = sql_db.Column(sql_db.Unicode, nullable=False)
    email = sql_db.Column(sql_db.Unicode, nullable=False)
    phone = sql_db.Column(sql_db.Unicode, nullable=False)
    password = sql_db.Column(sql_db.Unicode, nullable=False)

sql_db.create_all()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db = sql_db)
manager.create_api(User, collection_name='users', methods=['GET','POST','PUT','DELETE'])

app.run(port = be_port, debug = True)