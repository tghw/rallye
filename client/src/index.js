import Vue from 'vue'
import VueRouter from 'vue-router'
import VueResource from 'vue-resource'
import VueMoment from 'vue-moment';
import MomentTZ from 'moment-timezone';
import BootstrapVue from "bootstrap-vue";

// CSS
import "bootstrap/dist/css/bootstrap.css"
import "bootstrap-vue/dist/bootstrap-vue.css"

import Dashboard from './dashboard.vue'
import Driver from './driver.vue'
 
Vue.use(VueRouter);
Vue.use(VueResource);
Vue.use(VueMoment, {MomentTZ});
Vue.use(BootstrapVue);

var router = new VueRouter({
  mode: 'history',
  history: true,
  routes: [
    { path: '/', component: Dashboard },
    { path: '/driver', component: Driver },
  ]
});

const app = new Vue({
  el: '#app',
  router: router,
});
