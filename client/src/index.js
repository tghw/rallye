import Vue from 'vue'
import VueRouter from 'vue-router'
import VueResource from 'vue-resource'
import BootstrapVue from "bootstrap-vue";

// CSS
import "bootstrap/dist/css/bootstrap.css"
import "bootstrap-vue/dist/bootstrap-vue.css"

import Dashboard from './dashboard.vue'
 
Vue.use(VueRouter);
Vue.use(VueResource);
Vue.use(BootstrapVue);

var router = new VueRouter({
  mode: 'history',
  history: true,
  routes: [
    { path: '/', component: Dashboard },
  ]
});

const app = new Vue({
  el: '#app',
  router: router,
});

