<style scoped lang="less">

</style>

<template>
<div>
    <br>
    <h1 class="text-right">
    {{dttot(time)}}
    </h1>
    <div class="card">
        <div class="card-header"><h2>Current Leg</h2></div>
        <div class="card-body">
            <div class="row" v-if="leg">
                <div class="col">
                    Perfect
                    <br>
                    {{stom(leg.perfect)}}
                </div>
                <div class="col">
                    Elapsed
                    <br>
                    {{stom(leg.current)}}
                </div>
                <div class="col">
                    Difference
                    <br>
                    <span :class="leg.current > leg.perfect ? 'text-danger' : 'text-success'">{{Math.round(leg.current - leg.perfect)}}</span>
                </div>
                <div class="col">
                    Distance
                    <br>
                    {{num(leg.distance)}}
                </div>
                <div class="col">
                    Time Out
                    <br>
                    {{dttot(leg.time_out)}}
                    <br>
                    <button class="btn btn-link">Edit</button>
                </div>
                <div class="col">
                    <button @click="checkpoint()" class="btn btn-default btn-lg btn-block">&#10003;&bull;</button>
                </div>
                <div class="col">
                    <button @click="diy_checkpoint()" class="btn btn-default btn-lg btn-block">DIY &#10003;&bull;</button>
                </div>
                <div class="col">
                    <button @click="transit()" class="btn btn-default btn-lg btn-block">+ Transit</button>
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
                    <button @click="start_leg()" class="btn btn-default btn-block">Start New Leg</button>
                </div>
                <div class="col"></div>
            </div>
        </div>
    </div>
    <br>
    <div class="row">
        <div class="col">
            <div class="card">
                <div class="card-header">
                    <h2>Current CAST</h2>
                </div>
                <div class="card-body">
                    <div class="row" v-if="cast">
                        <div class="col">
                            CAST
                            <br>
                            {{num(cast.cast)}}
                        </div>
                        <div class="col">
                            Average
                            <br>
                            <span :class="cast.cast > cast.speed ? 'text-danger' : 'text-success'">
                                {{num(cast.speed)}}
                            </span>
                        </div>
                        <div class="col">
                            Current
                            <br>
                            {{num(cast.current_speed)}}
                        </div>
                        <div class="col">
                            Distance
                            <br>
                            {{num(cast.distance)}}
                        </div>
                        <div class="col">
                            <button @click="error()" class="btn btn-default btn-lg btn-block">Error</button>
                        </div>
                    </div>
                    <div class="row" v-else>
                        <div class="col">
                            Waiting on next leg to begin...
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col">
            <div class="card">
                <div class="card-header">
                    <h2>Next CAST</h2>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST">
                        </div>
                        <div class="col">
                            <button @click="next_cast()" class="btn btn-default btn-block">Go</button>
                        </div>
                        <div class="col">
                            <button @click="skip_cast()" class="btn btn-default btn-block">Skip</button>
                        </div>
                    </div>
                    <br>
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST">
                        </div>
                    </div>
                    <br>
                    <div class="row">
                        <div class="col-4">
                            <input class="form-control" type="number" placeholder="CAST">
                        </div>
                    </div>
                </div>
            </div>
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
            cast: {},
            time: new Date(),
        };
    },
    computed: {
    },
    methods: {
        dttot (dt) {
            if (!dt) return;
            if (!_.isDate(dt)) {
                dt = new Date(dt);
            }
            return this.zpad(dt.getHours()) + ':' + this.zpad(dt.getMinutes()) + ':' + this.zpad(dt.getSeconds());
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
            this.$http.get('/leg/current').then((resp) => {
                this.leg = resp.body;
            });
            this.$http.get('/cast/current').then((resp) => {
                this.cast = resp.body;
            });
        },
        checkpoint() {
            this.$http.post('/checkpoint').then((resp) => {
                var leg = resp.body;
            });
        },
        diy_checkpoint() {
            this.$http.post('/diy_checkpoint').then((resp) => {
                var data = resp.body;
            });
        },
        start_leg() {
            var out_str = this.$refs.start_time_out.value;
            var time_out = null
            if (out_str.length == 6) {
                var h = parseInt(out_str.substring(0, 2));
                var m = parseInt(out_str.substring(2, 4));
                var s = parseInt(out_str.substring(4, 6));
                var now = new Date();
                time_out = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s);
            }
            var cast = parseFloat(this.$refs.start_cast.value);
            this.$http.post('/new_leg', JSON.stringify({time_out: time_out, cast: cast})).then(this.update);
        },
    },
    mounted() {
        this.update();
        setInterval(this.update, 1000);
        setInterval(() => this.time = new Date(), 50);
    },
};
</script>

