import json
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from sqlalchemy import update
from sqlalchemy.ext.declarative import declarative_base
import flask_restless

DIY_MINUTES = 2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://rallye:rallye@192.168.1.126/rallye'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Calibration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulses = db.Column(db.Integer, default=360000)
    miles = db.Column(db.Float, default=1.0)

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
    transit = db.Column(db.Integer, nullable=True)

    def as_dict(self):
        return {name: getattr(self, name) for name in ([c.name for c in self.__table__.columns] + ['distance', 'perfect', 'current'])}

    @property
    def distance(self):
        return self.pulses * 1.0 / Calibration.ppm()

    @property
    def perfect(self):
        return sum([c.perfect for c in self.casts]) + (self.transit or 0)

    @property
    def current(self):
        return ((self.time_in or datetime.utcnow()) - self.time_out).total_seconds()

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

    def as_dict(self):
        return {name: getattr(self, name) for name in ([c.name for c in self.__table__.columns] + ['distance', 'perfect', 'current', 'speed', 'current_speed', 'start'])}

    @property
    def perfect(self):
        """
        Returns number of seconds.
        """
        return self.distance * 3600.0 / self.cast

    @property
    def current(self):
        return ((self.dt_end or datetime.utcnow()) - self.start).total_seconds()

    @property
    def distance(self):
        return self.pulses * 1.0 / Calibration.ppm()

    @property
    def speed(self):
        if not self.current:
            return 0.0
        return self.distance * 3600.0 / self.current

    @property
    def current_speed(self):
        return Count.current_speed()


    @property
    def start(self):
        return max(self.dt_start, self.leg.time_out)

    @property
    def leg(self):
        return db.session.query(Leg).get(self.leg_id)

    @staticmethod
    def current_cast():
        # Most recently started first.
        return db.session.query(Cast).filter(Cast.dt_end == None).order_by(Cast.dt_start.desc()).first()

    @staticmethod
    def new(speed):
        now = datetime.utcnow()
        new = Cast(cast=speed, leg_id=Leg.current_leg().id, dt_start=now)
        old = Cast.current_cast()
        if old:
            old.dt_end = now
            new.prev_id = old.id
        db.session.add(new)
        db.session.commit()
        db.session.refresh(new)
        return new

class Error(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dt = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    leg_id = db.Column(db.Integer, db.ForeignKey('leg.id'))
    corrected = db.Column(db.Boolean, nullable=False, default=False)
    distance = db.Column(db.Integer, nullable=False, default=0)
    turn_around = db.Column(db.DateTime, nullable=True)
    on_course = db.Column(db.DateTime, nullable=True)

    def back_on_course(self):
        self.on_course = datetime.utcnow()
        self.distance = db.session.query(func.sum(Count.a)).filter(Count.dt > self.turn_around, Count.dt < self.on_course).first()[0] * 2
        db.session.commit()
        self.correct()

    def correct(self):
        leg = Leg.current_leg()
        cast = Cast.current_cast()
        distance = self.distance
        while distance > 0 and cast:
            to_remove = min(distance, cast.pulses)
            cast.pulses -= to_remove
            if leg:
                leg.pulses -= to_remove
            distance -= to_remove
            if cast.prev_id:
                cast = db.session.query(Cast).get(cast.prev_id)
            else:
                cast = None
        self.corrected = True
        db.session.commit()

    def as_dict(self):
        return {name: getattr(self, name) for name in ([c.name for c in self.__table__.columns] + [])}

    @staticmethod
    def current_error():
        return db.session.query(Error).filter(Error.turn_around != None, Error.on_course == None).order_by(Error.dt.desc()).first()

db.create_all()
calibration = db.session.query(Calibration).filter(Calibration.id == 1).first()
if not calibration:
    db.session.add(Calibration())
db.session.commit()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Leg, methods=['GET', 'POST', 'PUT', 'DELETE'], include_methods=['distance', 'perfect', 'current'])
manager.create_api(Cast, methods=['GET', 'POST', 'PUT', 'DELETE'], include_methods=['perfect', 'current', 'distance', 'speed', 'current_speed',])
manager.create_api(Error, methods=['GET', 'POST', 'PUT'])
manager.create_api(Calibration, methods=['GET', 'PUT'])

# Views
@app.route('/update')
def update_data():
    leg = Leg.current_leg()
    if leg:
        leg = leg.as_dict()
    cast = Cast.current_cast()
    if cast:
        cast = cast.as_dict()
    error = Error.current_error()
    if error:
        error = error.as_dict()
    return json.dumps({'leg': leg, 'cast': cast, 'error': error}, default=str), 200, {'Content-Type': 'application/json'}

@app.route('/new_cast', methods=['POST'])
def new_cast():
    cast = Cast.new(request.json['speed'])
    return redirect('/api/cast/%d' % cast.id)

@app.route('/new_leg', methods=['POST'])
def new_leg():
    time_out = request.json['time_out'] or datetime.utcnow()
    cast = request.json['cast']
    leg = Leg(dt_start=datetime.utcnow(), time_out=time_out)
    db.session.add(leg)
    db.session.commit()
    db.session.refresh(leg)
    if cast:
        cast = Cast(dt_start=time_out, cast=cast, leg_id=leg.id)
        db.session.add(cast)
    db.session.commit()
    return redirect('/api/leg/%d' % leg.id)


@app.route('/error/manual', methods=['POST'])
def manual_error():
    distance = request.json['distance']
    pulses = distance * Calibration.ppm()
    error = Error(distance=pulses)
    db.session.add(error)
    db.session.commit()
    error.correct()
    return 'OK'

@app.route('/error/turnaround', methods=['POST'])
def turn_around_error():
    error = Error(turn_around=datetime.utcnow())
    db.session.add(error)
    db.session.commit()
    return json.dumps({'error': error.as_dict()}, default=str), 200, {'Content-Type': 'application/json'}

@app.route('/error/oncourse', methods=['POST'])
def on_course_error():
    error = Error.current_error()
    if not error:
        return 'No Error', 400
    error.back_on_course()
    return 'OK'

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
    leg.time_in = leg.time_out + timedelta(seconds=leg.perfect)
    cast = Cast.current_cast()
    if cast:
        cast.dt_end = leg.dt_end
    time_out = leg.time_in + timedelta(seconds=DIY_MINUTES * 60)
    new_leg = Leg(dt_start=datetime.utcnow(), time_out=time_out)
    db.session.add(new_leg)
    db.session.commit()
    db.session.refresh(new_leg)
    db.session.commit()
    return json.dumps({'time_in': leg.time_in, 'time_out': time_out}, default=str), 200, {'Content-Type': 'application/json'}

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

@app.route('/reset', methods=['POST'])
def reset():
    db.session.query(Count).delete()
    db.session.query(Cast).delete()
    db.session.query(Leg).delete()
    db.session.query(Error).delete()
    db.session.commit()
    return 'OK'

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)

