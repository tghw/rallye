<style>
h1.time {
    font-family: monospace;
}
.big {
    font-size: 2.4em;
}
</style>

<template>
<div class="big" @mousedown="startVideo">
    <p class="text-center time">
    {{dttot(time)}}
    </p>
    <div class="row text-center" v-if="leg">
        <div class="col">
            CAST<br>{{num(cast.cast)}}
        </div>
        <div class="col">
            Current<br>{{num(current_speed)}}
        </div>
        <div class="col">
            Difference<br><span :class="leg.current > leg.perfect ? 'text-danger' : 'text-success'">{{Math.round(leg.current - leg.perfect) || 0}}</span>
        </div>
    </div>
    <hr>
    <div class="row text-center mt-4" v-if="leg">
        <div class="col">
            Perfect<br>{{stom(leg.perfect)}}
        </div>
        <div class="col">
            Elapsed<br>{{stom(leg.current)}}
        </div>
        <div class="col">
            Time Out<br>{{dttot(leg.time_out)}}
        </div>
    </div>
    <hr>
    <div class="row text-center mt-4" v-if="leg">
        <div class="col">
            CAST Dist<br>{{num(cast.distance)}}
        </div>
        <div class="col">
            Leg Dist<br>{{num(leg.distance)}}
        </div>
    </div>
    <video loop ref="video">
        <source :src="mp4Source" type="video/mp4" />
        <source :src="webmSource" type="video/webm" />
    </video>
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
            current_speed: 0,
            addingTime: false,
            diy: {},
            error: null,
            calibrationMiles: 0,
            updateInterval: null,
            webmSource: 'data:video/webm;base64,GkXfo0AgQoaBAUL3gQFC8oEEQvOBCEKCQAR3ZWJtQoeBAkKFgQIYU4BnQI0VSalmQCgq17FAAw9CQE2AQAZ3aGFtbXlXQUAGd2hhbW15RIlACECPQAAAAAAAFlSua0AxrkAu14EBY8WBAZyBACK1nEADdW5khkAFVl9WUDglhohAA1ZQOIOBAeBABrCBCLqBCB9DtnVAIueBAKNAHIEAAIAwAQCdASoIAAgAAUAmJaQAA3AA/vz0AAA=',
            mp4Source: 'data:video/mp4;base64,AAAAHGZ0eXBpc29tAAACAGlzb21pc28ybXA0MQAAAAhmcmVlAAAAG21kYXQAAAGzABAHAAABthADAowdbb9/AAAC6W1vb3YAAABsbXZoZAAAAAB8JbCAfCWwgAAAA+gAAAAAAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAIVdHJhawAAAFx0a2hkAAAAD3wlsIB8JbCAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAIAAAACAAAAAABsW1kaWEAAAAgbWRoZAAAAAB8JbCAfCWwgAAAA+gAAAAAVcQAAAAAAC1oZGxyAAAAAAAAAAB2aWRlAAAAAAAAAAAAAAAAVmlkZW9IYW5kbGVyAAAAAVxtaW5mAAAAFHZtaGQAAAABAAAAAAAAAAAAAAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAEcc3RibAAAALhzdHNkAAAAAAAAAAEAAACobXA0dgAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAIAAgASAAAAEgAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABj//wAAAFJlc2RzAAAAAANEAAEABDwgEQAAAAADDUAAAAAABS0AAAGwAQAAAbWJEwAAAQAAAAEgAMSNiB9FAEQBFGMAAAGyTGF2YzUyLjg3LjQGAQIAAAAYc3R0cwAAAAAAAAABAAAAAQAAAAAAAAAcc3RzYwAAAAAAAAABAAAAAQAAAAEAAAABAAAAFHN0c3oAAAAAAAAAEwAAAAEAAAAUc3RjbwAAAAAAAAABAAAALAAAAGB1ZHRhAAAAWG1ldGEAAAAAAAAAIWhkbHIAAAAAAAAAAG1kaXJhcHBsAAAAAAAAAAAAAAAAK2lsc3QAAAAjqXRvbwAAABtkYXRhAAAAAQAAAABMYXZmNTIuNzguMw==',
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
                this.leg = resp.body.leg || {};
                this.cast = resp.body.cast || {};
                this.error = resp.body.error;
                this.time = resp.body.time;
                this.current_speed = resp.body.current_speed;
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
        startVideo() {
            this.$refs.video.play();
        },
    },
    mounted() {
        this.update();
        this.updateInterval = setInterval(this.update, 1000);
        this.$moment.tz.setDefault('UTC');
        this.$refs.video.play();
    },
    beforeDestroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    },
};
</script>

