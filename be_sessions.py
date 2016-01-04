from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import flask_restless

import uuid, OpenSSL

from datetime import datetime, timedelta

# Backend for sessions
# Sessions table is located in in-memory database
# Secure session ID is generated through OpenSSL

be_port = 5001
db_path = 'sqlite:///:memory:'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_path
memory_db = SQLAlchemy(app)

def sess_id_generate():
	uid = uuid.UUID(bytes = OpenSSL.rand.bytes(16))
	return uid.hex

class Session(memory_db.Model):
    __tablename__ = 'sessions'
    id = memory_db.Column(memory_db.String(32), primary_key=True, default = sess_id_generate)
    user_id = memory_db.Column(memory_db.Unicode)
    last_used = memory_db.Column(memory_db.DateTime, nullable=False)

memory_db.create_all()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db = memory_db)
manager.create_api(Session, collection_name='sessions', methods=['GET','POST','PUT','PATCH','DELETE'])
	
app.run(port = be_port, debug = True)