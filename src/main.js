import Vue from 'vue'
import VueBlobJsonCsv from 'vue-blob-json-csv';
import { BootstrapVue, IconsPlugin, BFormTimepicker } from 'bootstrap-vue'
import App from './App.vue'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import router from "./router/routes.js"
import VueSocketIO from 'vue-socket.io'
import SocketIO from "socket.io-client"
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'

// import ECharts modules manually to reduce bundle size
import {
  CanvasRenderer
} from 'echarts/renderers'
import {
  BarChart,
  LineChart
} from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  ToolboxComponent
} from 'echarts/components'

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  ToolboxComponent,
  LineChart
]);

Vue.use(BootstrapVue)
Vue.use(IconsPlugin)
Vue.use(VueBlobJsonCsv)
Vue.use(
  new VueSocketIO({
    debug: true ,   // debug调试，生产建议关闭
    connection: SocketIO("10.60.150.29:5000/test_conn"),
  })
)
Vue.component('b-form-timepicker', BFormTimepicker)
Vue.component('v-chart', ECharts)
Vue.config.productionTip = false

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
