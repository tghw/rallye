#!/usr/bin/env python

import sys
from serial import Serial
from daemon import Daemon
from server import db, Count

class Updater(Daemon):
    def __init__(self, *args, **kwargs):
        super(Updater, self).__init__(*args, **kwargs)
        self.usb = Serial('/dev/ttyUSB0')
        self.a = 0
        self.b = 0

    def run(self):
        while True:
            try:
                print('Is active: %s' % db.session.is_active)
                line = self.usb.readline().strip()
                a, b = (int(x) for x in line.split(b'|'))
                self.a += a
                self.b += b
                db.session.add(Count(a=self.a, b=self.b))
                db.session.commit()
                self.a = 0
                self.b = 0
            except Exception as e:
                db.session.rollback()
                sys.stderr.write('%s\n' % e)

if __name__ == '__main__':
    updater = Updater('/tmp/rallye.pid', stdout='/tmp/rallye.stdout', stderr='/tmp/rallye.stderr')
    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            updater.start()
        elif sys.argv[1] == 'stop':
            updater.stop()
        elif sys.argv[1] == 'restart':
            updater.restart()
        else:
            print('Unknown command')
            sys.exit(2)
        sys.exit(0)
    else:
        print('Usage: %s start|stop|restart' % sys.argv[0])
        sys.exit(2)

