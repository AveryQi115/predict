import Vue from 'vue'
import VueBlobJsonCsv from 'vue-blob-json-csv';
import { BootstrapVue, IconsPlugin, BFormTimepicker } from 'bootstrap-vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import router from "./router/routes.js";

Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(VueBlobJsonCsv)
Vue.component('b-form-timepicker', BFormTimepicker)
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
