<style>
h1.time {
    font-family: monospace;
}
</style>

<template>
<div>
    <br>
    <h1 class="text-right time">
    {{dttot(time)}}
    </h1>
    <div class="row text-center">
        <div class="col">
            CAST<br>{{num(cast.cast)}}
        </div>
        <div class="col">
            Average<br><span :class="cast.cast > cast.speed ? 'text-danger' : 'text-success'">{{num(cast.speed)}}</span>
        </div>
        <div class="col">
            Current<br>{{num(cast.current_speed)}}
        </div>
    </div>
    <div class="row text-center mt-4" v-if="leg">
        <div class="col">
            Perfect<br>{{stom(leg.perfect)}}
        </div>
        <div class="col">
            Elapsed<br>{{stom(leg.current)}}
        </div>
        <div class="col">
            Difference<br><span :class="leg.current > leg.perfect ? 'text-danger' : 'text-success'">{{Math.round(leg.current - leg.perfect)}}</span>
        </div>
    </div>
    <div class="row text-center mt-4" v-if="leg">
        <div class="col">
            CAST Distance<br>{{num(cast.distance)}}
        </div>
        <div class="col">
            Leg Distance<br>{{num(leg.distance)}}
        </div>
        <div class="col">
            Time Out<br>{{dttot(leg.time_out)}}
        </div>
    </div>
</div>
</template>

<script>
import _ from 'underscore';
import humanize from 'humanize-plus';
export default {
    data() {
        return {
            leg: {},
            last_leg: {},
            cast: {},
            time: new Date(),
            addingTime: false,
            diy: {},
            error: null,
            calibrationMiles: 0,
            updateInterval: null,
            timeInterval: null,
        };
    },
    computed: {
    },
    methods: {
        dttot (dt) {
            if (!dt) return;
            if (_.isString(dt)) {
                dt = this.$moment(dt).tz('UTC').tz('America/Denver');
            }
            else {
                dt = this.$moment(dt).tz('America/Denver');
            }
            return dt.format('HH:mm:ss');
        },
        zpad(x) {
            return ('' + x).padStart(2, '0');
        },
        num(x) {
            if (!x) return 0;
            return humanize.formatNumber(x, 2);
        },
        stom(x) {
            if (!x) return '0:00';
            var neg = '';
            if (x < 0) {
                neg = '-';
                x = -1 * x;
            }
            return neg + parseInt(Math.round(x) / 60) + ':' + this.zpad(parseInt(Math.round(x) % 60));
        },
        update() {
            this.$http.get('/update').then((resp) => {
                this.leg = resp.body.leg;
                this.cast = resp.body.cast;
                this.error = resp.body.error;
            });
        },
        checkpoint() {
            this.last_leg = {};
            this.$refs.checkPointModal.show();
            this.$http.post('/checkpoint').then((resp) => {
                this.last_leg = resp.body;
            });
        },
        diy_checkpoint() {
            this.diy = {};
            this.$refs.diyCheckPointModal.show();
            this.$http.post('/diy_checkpoint').then((resp) => {
                this.diy = resp.body;
            });
        },
        start_leg() {
            var out_str = this.$refs.start_time_out.value;
            var time_out = this.parseTimeOut(out_str);
            if (!time_out) time_out = this.$moment(new Date());
            var cast = parseFloat(this.$refs.start_cast.value);
            this.$http.post('/new_leg', JSON.stringify({time_out: time_out.format(), cast: cast})).then(this.update);
        },
        next_cast() {
            var new_speed = parseInt(this.$refs.cast1.value);
            if (new_speed) {
                this.$http.post('/new_cast', JSON.stringify({speed: new_speed})).then(this.update);
            }
            this.skip_cast();
        },
        skip_cast() {
            this.$refs.cast1.value = this.$refs.cast2.value;
            this.$refs.cast2.value = this.$refs.cast3.value;
            this.$refs.cast3.value = '';
        },
        parseTimeOut(out_str) {
            var time_out = null;
            if (out_str.length == 6) {
                var h = parseInt(out_str.substring(0, 2));
                var m = parseInt(out_str.substring(2, 4));
                var s = parseInt(out_str.substring(4, 6));
                var now = new Date();
                time_out = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s);
                time_out = this.$moment(time_out).tz('America/Denver').tz('UTC');
            }
            return time_out;
        },
        editTimeOut(e) {
            e.preventDefault();
            var time_out = this.parseTimeOut(this.$refs.editTimeOut.localValue);
            this.$http.put(`/api/leg/${this.leg.id}`, JSON.stringify({time_out: time_out.format('YYYY-MM-DDTHH:mm:ss')})).then(() => {
                this.$refs.editTimeOutModal.hide();
            });
        },
        beginTransit(e) {
            e.preventDefault();
            var mins = parseInt(this.$refs.transitTime.localValue);
            var transit = (this.leg.transit || 0) + mins * 60;
            if (this.cast) {
                this.$http.put(`/api/cast/${this.cast.id}`, JSON.stringify({dt_end: 'CURRENT_TIMESTAMP'}));
            }
            this.$http.put(`/api/leg/${this.leg.id}`, JSON.stringify({transit: transit})).then(() => {
                this.$refs.transitModal.hide();
            });
        },
        addTime(e) {
            e.preventDefault();
            var mins = parseInt(this.$refs.addTime.localValue);
            this.pause(mins * 60, true);
        },
        pause(sec, hide) {
            if (sec > 0) {
                var transit = (this.leg.transit || 0) + sec;
                this.addingTime = true;
                this.$http.put(`/api/leg/${this.leg.id}`, JSON.stringify({transit: transit})).then(() => {
                    this.addingTime = false;
                    if (hide) {
                        this.$refs.addTimeModal.hide();
                    }
                });
            }
            else if (hide) {
                    this.$refs.addTimeModal.hide();
            }
        },
        errorStart() {
            this.$refs.errorModal.show();
        },
        errorTurnAround() {
            this.$http.post('/error/turnaround');
        },
        errorOnCourse() {
            this.$http.post('/error/oncourse');
            this.$refs.errorModal.hide();
        },
        errorManualDistance() {
            this.$http.post('/error/manual', JSON.stringify({'distance': parseFloat(this.$refs.errorMiles.localValue)}));
            this.$refs.errorModal.hide();
        },
        calibrate() {
            var pulses = this.last_leg.pulses;
            var miles = this.$refs.calibrationMiles.localValue;
            this.$http.post('/calibrate', JSON.stringify({miles: miles, pulses: pulses}));
        },
        reset() {
            this.$http.post('/reset');
        },
    },
    mounted() {
        this.update();
        this.updateInterval = setInterval(this.update, 1000);
        this.timeInterval = setInterval(() => this.time = new Date(), 50);
        this.$moment.tz.setDefault('UTC');
    },
    beforeDestroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        if (this.timeInterval) {
            clearInterval(this.timeInterval);
            this.timeInterval = null;
        }
    },
};
</script>

