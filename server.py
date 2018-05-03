from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://rallye:rallye@localhost/rallye'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    a = db.Column(db.Integer, nullable=False)
    b = db.Column(db.Integer, nullable=False)

class Leg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, nullable=True)
    prev_id = db.Column(db.Integer, db.ForeignKey('leg.id'), nullable=True)
    nexts = db.relationship('Leg')
    casts = db.relationship('Cast')

    def distance(self):
        q = db.session.query(func.sum(Count.a).label('pulses')).filter(Count.dt > self.dt_start)
        if self.dt_end:
            q = q.filter(Count.dt < self.dt_end)
        return q.first()[0]

class Cast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    leg_id = db.Column(db.Integer, db.ForeignKey('leg.id'))
    dt_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, nullable=True)
    prev_id = db.Column(db.Integer, db.ForeignKey('cast.id'), nullable=True)
    nexts = db.relationship('Cast')

    def distance(self):
        q = db.session.query(func.sum(Count.a).label('pulses')).filter(Count.dt > self.dt_start)
        if self.dt_end:
            q = q.filter(Count.dt < self.dt_end)
        return q.first()[0]

    def speed(self):
        d = self.distance()
        t = (self.dt_end or datetime.utcnow()) - self.dt_start
        return d * 1.0 / t.total_seconds()

db.create_all()
db.session.commit()
