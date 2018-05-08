import json
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy import update
import flask_restless

DIY_MINUTES = 2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://rallye:rallye@localhost/rallye'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Calibration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulses = db.Column(db.Integer, default=360000)
    miles = db.Column(db.Float, default = 1.0)
    
    @staticmethod
    def ppm():
        c = db.session.query(Calibration).get(1)
        return int(c.pulses * 1.0 / c.miles)

    @staticmethod
    def update(pulses, miles):
        c = db.session.query(Calibration).get(1)
        c.pulses = pulses
        c.miles = miles
        db.session.commit()

class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    a = db.Column(db.Integer, nullable=False)
    b = db.Column(db.Integer, nullable=False)

    @staticmethod
    def current_speed():
        samples = 3
        cs = db.session.query(Count).order_by(Count.dt.desc()).limit(samples + 1).all()
        ppm = Calibration.ppm()
        l = []
        for i in range(len(cs) - 1):
            p = cs[i].a
            s = (cs[i].dt - cs[i+1].dt).total_seconds()
            l.append(3600.0 * p / (ppm * s))
        return (sum(l) + l[0]) / (len(l) + 1) # Average to remove noise, with extra weight on the most recent.

class Leg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, nullable=True)
    time_out = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_in = db.Column(db.DateTime, nullable=True)
    prev_id = db.Column(db.Integer, db.ForeignKey('leg.id'), nullable=True)
    nexts = db.relationship('Leg')
    casts = db.relationship('Cast')
    pulses = db.Column(db.Integer, nullable=False, default=0)

    @property
    def distance(self):
        return self.pulses * 1.0 / Calibration.ppm()

    @property
    def perfect(self):
        return sum([c.perfect for c in self.casts])

    @property
    def current(self):
        return ((self.dt_end or datetime.utcnow()) - self.dt_start).total_seconds()

    @staticmethod
    def current_leg():
        # Most recently started first.
        return db.session.query(Leg).filter(Leg.dt_end == None).order_by(Leg.dt_start.desc()).first()

class Cast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    leg_id = db.Column(db.Integer, db.ForeignKey('leg.id'))
    cast = db.Column(db.Integer, nullable=False, default=-1)
    dt_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    dt_end = db.Column(db.DateTime, nullable=True)
    prev_id = db.Column(db.Integer, db.ForeignKey('cast.id'), nullable=True)
    nexts = db.relationship('Cast')
    pulses = db.Column(db.Integer, nullable=False, default=0)

    @property
    def perfect(self):
        """
        Returns number of seconds.
        """
        return self.distance * 3600.0 / self.cast

    @property
    def current(self):
        return ((self.dt_end or datetime.utcnow()) - self.dt_start).total_seconds()

    @property
    def distance(self):
        return self.pulses * 1.0 / Calibration.ppm()

    @property
    def speed(self):
        return self.distance * 3600.0 / self.current

    @property
    def current_speed(self):
        return Count.current_speed()

    @staticmethod
    def current_cast():
        # Most recently started first.
        return db.session.query(Cast).filter(Cast.dt_end == None).order_by(Cast.dt_start.desc()).first()

    @staticmethod
    def new(speed):
        now = datetime.utcnow() 
        old = Cast.current_cast()
        old.dt_end = now
        new = Cast(cast=speed, leg_id=Leg.current_leg().id, dt_start=now, prev_id=old.id)
        db.session.add(new)
        db.session.commit()
        db.session.refresh(new)
        return new

db.create_all()
calibration = db.session.query(Calibration).filter(Calibration.id == 1).first()
if not calibration:
    db.session.add(Calibration())
db.session.commit()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Leg, methods=['GET', 'POST', 'PUT', 'DELETE'], include_methods=['distance', 'perfect', 'current'])
manager.create_api(Cast, methods=['GET', 'POST', 'PUT', 'DELETE'], include_methods=['perfect', 'current', 'distance', 'speed', 'current_speed',])
manager.create_api(Calibration, methods=['GET', 'PUT'])

# Views
@app.route('/update')
def update():
    return ''

@app.route('/new_cast', methods=['POST'])
def new_cast():
    cast = Cast.new(request.json['speed'])
    return redirect('/api/cast/%d' % cast.id)

@app.route('/new_leg', methods=['POST'])
def new_leg():
    time_out = request.json['time_out'] or datetime.utcnow()
    cast = request.json['cast']
    leg = Leg(dt_start=time_out)
    db.session.add(leg)
    db.session.commit()
    db.session.refresh(leg)
    cast = Cast(dt_start=time_out, cast=cast, leg_id=leg.id)
    db.session.add(cast)
    db.session.commit()
    return redirect('/api/leg/%d' % leg.id)

@app.route('/checkpoint', methods=['POST'])
def checkpoint():
    now = datetime.utcnow()
    leg = Leg.current_leg()
    leg.dt_end = now
    leg.time_in = now
    cast = Cast.current_cast()
    if cast:
        cast.dt_end = leg.dt_end
    db.session.commit()
    return redirect('/api/leg/%d' % leg.id)

@app.route('/diy_checkpoint', methods=['POST'])
def diy_checkpoint():
    now = datetime.utcnow()
    leg = Leg.current_leg()
    leg.dt_end = now
    leg.time_in = leg.dt_start + timedelta(seconds=leg.perfect)
    cast = Cast.current_cast()
    if cast:
        cast.dt_end = leg.dt_end
    time_out = leg.dt_end + timedelta(seconds=DIY_MINUTES * 60)
    new_leg = Leg(dt_start=time_out)
    db.session.add(new_leg)
    db.session.commit()
    db.session.refresh(new_leg)
    cast = Cast(dt_start=time_out, cast=30, leg_id=new_leg.id)
    db.session.add(cast)
    db.session.commit()
    return json.dumps({'time_in': leg.dt_end, 'time_out': time_out}, default=str), 200, {'Content-Type': 'application/json'}

@app.route('/leg/current')
def current_leg():
    leg = Leg.current_leg()
    if leg:
        return redirect('/api/leg/%d' % leg.id)
    return json.dumps(None), 200, {'Content-Type': 'application/json'}

@app.route('/cast/current')
def current_cast():
    cast = Cast.current_cast()
    if cast:
        return redirect('/api/cast/%d' % cast.id)
    return json.dumps(None), 200, {'Content-Type': 'application/json'}

@app.route('/s/<path:path>')
def static_files(path):
    return send_from_directory('client/dist', path)

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)

