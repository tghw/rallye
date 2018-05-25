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
    <b-button variant="default" v-b-modal.settingsModal>&#x2699;</b-button>
    </h1>
    <div class="card">
        <div class="card-header"><h2>Current Leg</h2></div>
        <div class="card-body">
            <div class="row text-center" v-if="leg">
                <div class="col">
                    Perfect<br>{{stom(leg.perfect)}}
                </div>
                <div class="col">
                    Elapsed<br>{{stom(leg.current)}}
                </div>
                <div class="col">
                    Difference<br><span :class="leg.current > leg.perfect ? 'text-danger' : 'text-success'">{{Math.round(leg.current - leg.perfect)}}</span>
                </div>
                <div class="col">
                    Distance<br>{{num(leg.distance)}}
                </div>
                <div class="col">
                    Time Out<br>{{dttot(leg.time_out)}}<br><b-button v-b-modal.editTimeOutModal variant="link">Edit</b-button>
                </div>
                <div class="col">
                    <b-button @click="checkpoint()" block size="lg" variant="primary">&#10003;&bull;</b-button>
                </div>
                <div class="col">
                    <b-button @click="diy_checkpoint()" size="lg" variant="success">DIY &#10003;&bull;</b-button>
                </div>
                <div class="col">
                    <b-button variant="default" block size="lg" v-b-modal.addTimeModal>+ Time</b-button>
                </div>
            </div>
            <div class="row" v-else>
                <div class="col">
                    <input type="number" class="form-control" ref="start_time_out" placeholder="Time Out HHMMSS">
                </div>
                <div class="col">
                    <input type="number" class="form-control" ref="start_cast" placeholder="Starting CAST">
                </div>
                <div class="col">
                    <b-button @click="start_leg()" block variant="primary">Start New Leg</b-button>
                </div>
                <div class="col"></div>
            </div>
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col-8">
            <div class="card">
                <div class="card-header">
                    <h2>Current CAST</h2>
                </div>
                <div class="card-body">
                    <div class="row text-center" v-if="cast">
                        <div class="col">
                            CAST<br>{{num(cast.cast)}}
                        </div>
                        <div class="col">
                            Average<br><span :class="cast.cast > cast.speed ? 'text-danger' : 'text-success'">{{num(cast.speed)}}</span>
                        </div>
                        <div class="col">
                            Current<br>{{num(cast.current_speed)}}
                        </div>
                        <div class="col">
                            Distance<br>{{num(cast.distance)}}
                        </div>
                        <div class="col">
                            <b-button @click="errorStart()" variant="danger" block>Error</b-button>
                        </div>
                    </div>
                    <div class="row" v-else>
                        <div class="col">
                            Waiting on next leg or CAST...
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-4">
            <div class="card">
                <div class="card-header">
                    <h2>Next CAST</h2>
                    <span class="pull-right">
                    <b-button variant="default" v-b-modal.transitModal>Begin Transit</b-button>
                    </span>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST" ref="cast1">
                        </div>
                        <div class="col">
                            <b-button @click="next_cast()" variant="primary" block>Go</b-button>
                        </div>
                        <div class="col">
                            <b-button @click="skip_cast()" variant="default" block>Skip</b-button>
                        </div>
                    </div>
                    <br>
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST" ref="cast2">
                        </div>
                    </div>
                    <br>
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST" ref="cast3">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <b-modal id="editTimeOutModal" title="Edit Time Out" ref="editTimeOutModal" @ok="editTimeOut">
        <b-form-input type="number" placeholder="Time Out HHMMSS" ref="editTimeOut" autofocus="autofocus" />
    </b-modal>
    <b-modal id="transitModal" ref="transitModal" title="Begin Transit" @ok="beginTransit">
        <p>Transit will begin when you press OK</p>
        <b-form-input type="number" placeholder="Transit (MM)" ref="transitTime" autofocus="autofocus" />
    </b-modal>
    <b-modal id="addTimeModal" ref="addTimeModal" title="Add Time" @ok="addTime">
        <b-form-input type="number" placeholder="Time (mins)" ref="addTime" autofocus="autofocus" />
        <br>
        <b-row>
            <b-col><b-button variant="default" block @click="pause(5)" :disabled="addingTime">5 Sec</b-button></b-col>
            <b-col><b-button variant="default" block @click="pause(10)" :disabled="addingTime">10 Sec</b-button></b-col>
            <b-col><b-button variant="default" block @click="pause(15)" :disabled="addingTime">15 Sec</b-button></b-col>
        </b-row>
        <br>
        <b-row>
            <b-col><b-button variant="default" block @click="pause(20)" :disabled="addingTime">20 Sec</b-button></b-col>
            <b-col><b-button variant="default" block @click="pause(30)" :disabled="addingTime">30 Sec</b-button></b-col>
            <b-col><b-button variant="default" block @click="pause(45)" :disabled="addingTime">45 Sec</b-button></b-col>
        </b-row>
    </b-modal>
    <b-modal id="checkPointModal" ref="checkPointModal" title="Checkpoint" ok-only>
        <div class="text-center">
            <h3>Time Out</h3>
            <p v-if="last_leg.time_out">{{dttot(last_leg.time_out)}}</p>
            <p v-else>Calculating...</p>
            <h3>Time In</h3>
            <p v-if="last_leg.time_in">{{dttot(last_leg.time_in)}}</p>
            <p v-else>Calculating...</p>
            <h3>Elapsed</h3>
            <p v-if="last_leg.current">{{stom(last_leg.current)}}</p>
            <p v-else>Calculating...</p>
            <h3>Perfect</h3>
            <p v-if="last_leg.perfect">{{stom(last_leg.perfect)}}</p>
            <p v-else>Calculating...</p>
            <h3>Difference</h3>
            <p v-if="last_leg.perfect">
                <span :class="last_leg.current > last_leg.perfect ? 'text-danger' : 'text-success'">{{Math.round(last_leg.current - last_leg.perfect)}}</span>
            </p>
            <p v-else>Calculating...</p>
            <p>
                <b-button variant="default" v-b-modal.calibrateModal>Calibrate</b-button>
            </p>
        </div>
    </b-modal>
    <b-modal id="diyCheckPointModal" ref="diyCheckPointModal" title="DIY Checkpoint" ok-only>
        <div class="text-center">
            <h3>Time In (Perfect)</h3>
            <p v-if="diy.time_in">{{dttot(diy.time_in)}}</p>
            <p v-else>Calculating...</p>
            <h3>Time Out</h3>
            <p v-if="diy.time_out">{{dttot(diy.time_out)}}</p>
            <p v-else>Calculating...</p>
        </div>
    </b-modal>
    <b-modal id="errorModal" ref="errorModal" title="Error" hide-footer>
        <b>Automatic Correction</b>
        <b-row>
            <b-col>
                <b-button variant="success" size="lg" block @click="errorOnCourse" v-if="error">On Course</b-button>
                <b-button variant="danger" size="lg" block @click="errorTurnAround" v-else>Turn Around</b-button>
            </b-col>
        </b-row>
        <b class="mt-3">Manual Correction</b>
        <b-row>
            <b-col>
            Distance (Miles)<br><b-form-input type="number" class="mb-1" ref="errorMiles" />
            <b-button block variant="warning" @click="errorManualDistance">Submit</b-button>
            </b-col>
        </b-row>
    </b-modal>
    <b-modal id="calibrateModal" ref="calibrateModal" @ok="calibrate">
        <h5>Measured</h5>
        <p>
            Miles: {{last_leg.distance}}
            <br>
            Pulses: {{last_leg.pulses}}
            <br>
            PPM: {{Math.round(last_leg.pulses / last_leg.distance)}}
        </p>
        <h5>Calibrated</h5>
        <p>
            Miles: <b-form-input ref="calibrationMiles" type="number" v-model="calibrationMiles" />
            <br>
            Pulses: {{last_leg.pulses}}
            <br>
            PPM: {{Math.round(last_leg.pulses / calibrationMiles)}}
        </p>
    </b-modal>
    <b-modal id="settingsModal" ref="settingsModal" ok-only>
        <b-button variant="primary" block v-b-modal.calibrateModal>Calibrate</b-button>
        <b-button variant="danger" block v-b-modal.resetModal>Reset</b-button>
    </b-modal>
    <b-modal id="resetModal" ref="resetModal" @ok="reset" ok-title="Reset">
        Are you sure you want to reset?
    </b-modal>
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
            cancelInterval(this.updateInterval);
            this.updateInterval = null;
        }
        if (this.timeInterval) {
            cancelInterval(this.timeInterval);
            this.timeInterval = null;
        }
    },
};
</script>

