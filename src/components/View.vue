<template>
    <div id="app">
      <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">Dynamic Deployment</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarColor01" aria-controls="navbarColor01" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbarColor01">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                    <b-link class="nav-link active" :to="{ path: '/'}" replace>Home
                        <span class="visually-hidden">(current)</span>
                    </b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Pods'}" replace>Predict</b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Nodes'}" replace>Scheduling</b-link>
                    </li>
                    <li class="nav-item">
                        <b-dropdown id="dropdown-1" text="Monitor" variant="dark">
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Pods'}" replace>Pods</b-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Services'}" replace>Services</b-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Deployments'}" replace>Deployments</b-link>
                            </b-dropdown-item>
                        </b-dropdown>
                    </li>
                </ul>
                </div>
            </div>
      </nav>
      <div class="page-header">
        <h1>Monitor Real Data and Predict Data</h1>
      </div>
      <div class="row">
        <div class="form-group">
          <label for="predictModel" class="form-label mt-4">Choose Predict Model</label>
          <select v-model="model_new" class="form-select" id="predictModel">
            <option>monitor</option>
            <option>integration</option>
            <option>lstm</option>
            <option>svr</option>
            <option>rf</option>
          </select>
        </div>
        <button type="submit" class="btn btn-primary" @click="switchModel">Switch</button>
      </div>
      <div class="row">
          <v-chart style="width: 480px;height:320px;" :option="mem"/>
          <v-chart style="width: 480px;height:320px;" :option="cpu"/>
          <v-chart style="width: 480px;height:320px;" :option="http"/>
      </div>

      <!-- <div style="display:flex">
          <v-chart :options="mem_evaluate"/>
          <v-chart :options="cpu_evaluate"/>
          <v-chart :options="http_evaluate"/>
      </div> -->
    </div>
</template>

<script>
  export default {
    name : 'test',
    data() {
      return {
        MODELS      : ['monitor', 'integration', 'lstm', 'svr', 'rf'],    // model type
        model_types : 5,                                                  // model type length
        data_types  : -1,                                                 // data type length, 根据数据动态更新，最大为3（mem, cpu, http）
        data_length : 30,                                                 // 图表最长显示数据长度
        model       : 'monitor',
        model_new   : '',
        subsribe_name: '',
        data_real   : new Array(),
        data_pred   : new Array(),
        data_mae    : new Array(),
        data_mape   : new Array(),
        data_rmse   : new Array(),
        time_old    : new Array(),
        update_count: new Array(),
        data_time   : new Array(),
        mem: {},
        cpu: {},
        http: {},
      }
    },
    created() {
      this.$socket.open();
      this.initData();
      this.initGraph();
      this.subsribe_name = this.$route.params.pod_name+'_'+this.model;
      this.$socket.emit('message', this.subsribe_name);
      this.sockets.subscribe(this.subsribe_name, this.updateData);
    },
    destroyed() {
      this.$socket.close()
    },
    beforeDestroy() {
      this.$socket.emit('stopPreviousSubscribe', this.subsribe_name)
      this.sockets.unsubscribe(this.subsribe_name)
    },
    methods: {
      generateGraphOption: function(title_name, time, real, predict){
        return {
          title: {
            text: title_name,
            x: 'center',
            textStyle: {
              "fontSize": 16
            }
          },
          tooltip: {
            trigger: 'axis'
          },
          // 调整图表在div中的大小
          grid: {
            top: "35px",
            left: "100px",
            right: "10px",
            bottom: "50px"
          },
          legend: {
            show: true,
            top: "6%",
            data: ['real', 'predict'],
            textStyle: {
              fontSize: 12
            },
            x: 'center'
          },
          toolbox: {
            show: true,
            feature: {
              mark: { show: true },
              dataView: { show: true, readOnly: false },
              magicType: { show: true, type: ['line'] },
              saveAsImage: { show: true }
            }
          },
          calculable: true,
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: time
          },
          yAxis: {
            type: 'value',
            min: 0,
            // max: 18000,
            splitNumber: 3
          },
          series: [{
              name: 'real',
              type: 'line',
              color: "blue",
              data: real
            },
            {
              name: 'predict',
              type: 'line',
              color: "red",
              data: predict
            }]
        };
      },
      initData:function(){
        // 初始化填充0
        for(let i = 0; i < this.model_types; i++) {                 // i=0,1,2,3(intergrated,lstm,svr,rf)
          this.data_real[this.MODELS[i]] = new Array();
          this.data_pred[this.MODELS[i]] = new Array();
          this.data_mae[this.MODELS[i]] = new Array();
          this.data_mape[this.MODELS[i]] = new Array();
          this.data_rmse[this.MODELS[i]] = new Array();
          this.time_old[this.MODELS[i]] = 0;
          this.update_count[this.MODELS[i]] = 0;
          this.data_time[this.MODELS[i]] = new Array();
          for(let j = 0; j < 3; j++) {                              // j = 0,1,2(mem, cpu, http)
            this.data_real[this.MODELS[i]][j] = new Array();
            this.data_pred[this.MODELS[i]][j] = new Array();
            this.data_mae[this.MODELS[i]][j] = new Array();
            this.data_mape[this.MODELS[i]][j] = new Array();
            this.data_rmse[this.MODELS[i]][j] = new Array();
          }
        }
        
        for(let k = 0; k < this.data_length; k++) {
          for(let i = 0; i < this.model_types; i++) {
            this.data_time[this.MODELS[i]].push(0);
            for(let j = 0; j < 3; j++) {
              this.data_pred[this.MODELS[i]][j].push(0);
              this.data_real[this.MODELS[i]][j].push(0);
              this.data_mae[this.MODELS[i]][j].push(0);
              this.data_mape[this.MODELS[i]][j].push(0);
              this.data_rmse[this.MODELS[i]][j].push(0);
            }
          }       
        }   // end of for
      },  // end of initGraph
      initGraph: function(){
        this.mem = this.generateGraphOption('内存占用率', this.data_time[this.model], this.data_real[this.model][0], this.data_pred[this.model][0]);
        this.cpu = this.generateGraphOption('CPU占用率', this.data_time[this.model], this.data_real[this.model][1], this.data_pred[this.model][1]);
        this.http = this.generateGraphOption('HTTP请求量', this.data_time[this.model], this.data_real[this.model][2], this.data_pred[this.model][2]);
      },
      updateData: function(data){
        data = data['data']
        // 更新数据图表
        if(this.data_types == -1)
          if(this.model=='monitor')
            this.data_types = data.length-1;  // data.length-1为去掉时间指标的剩余指标
          else
            this.data_types = (data.length-1)/2;
        
        console.log(this.data_types);
        // 检查时间
        if(data[0] == this.time_old[this.model]) {
            console.log(data[0]);
            return;
        }
        else
          this.time_old[this.model] = data[0];
        this.update_count[this.model] += 1;
        
        // 更新数据
        this.data_time[this.model].push(data[0]); // 更新时间戳

        for(let i = 0; i < this.data_types; i++) { // 更新预测值和真实值  
          if(this.model=='monitor'){
            this.data_real[this.model][i].push(data[i+1]);
            this.data_pred[this.model][i].push(0);
          } else {
            this.data_real[this.model][i].push(data[2*i+1]);
            console.log(data[2*i+1]);
            this.data_pred[this.model][i].push(data[2*i+2]);
            console.log(data[2*i+2]);
          }
        }

        this.mem = this.generateGraphOption('内存占用率', this.data_time[this.model].slice(-this.data_length), this.data_real[this.model][0].slice(-this.data_length), this.data_pred[this.model][0].slice(-this.data_length));
        this.cpu = this.generateGraphOption('CPU占用率', this.data_time[this.model].slice(-this.data_length), this.data_real[this.model][1].slice(-this.data_length), this.data_pred[this.model][1].slice(-this.data_length));
        this.http = this.generateGraphOption('HTTP请求量', this.data_time[this.model].slice(-this.data_length), this.data_real[this.model][2].slice(-this.data_length), this.data_pred[this.model][2].slice(-this.data_length));
        
        // if(update_count[this.model] % this.data_length == 0) { // 更新指标
        //     for(var i = 0; i < data_types; i++) {
        //         data_mae[model][i].push(cal_mae(data_pred[model][i], data_real[model][i]));
        //         data_mape[model][i].push(cal_mape(data_pred[model][i], data_real[model][i]));
        //         data_rmse[model][i].push(cal_rmse(data_pred[model][i], data_real[model][i]));
        //     }
        // }
      },
      switchModel: function(){
        this.$socket.emit('stopPreviousSubscribe', this.subsribe_name);
        this.sockets.unsubscribe(this.subsribe_name);
        this.model = this.model_new;
        this.subsribe_name = this.$route.params.pod_name+'_'+this.model;
        this.$socket.emit('message', this.subsribe_name);
        this.sockets.subscribe(this.subsribe_name, this.updateData);
        console.log("subscribe ", this.subsribe_name);
      }
    },  // end of methods
    sockets: {},
    mounted () {
      this.sockets.subscribe(this.subsribe_name, this.updateData)
    }
  }
</script>

<style>
@import "../../public/bootstrap.min.css";
.page-header {
    margin-top: 30px;
    margin-bottom: 30px;
}
</style>