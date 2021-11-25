$(function () {
    var MODELS = ['integration', 'lstm', 'svr', 'rf']; //预测模型的种类（集成、LSTM、SVR、RF）
    var model_types = MODELS.length; 
    var data_types_max = 3; //负载数据的种类（内存、CPU、HTTP）
    var data_types = -1;    //负载数据的种类（根据数据动态更新，不大于max值）
    var data_time = new Array(); //时间 二维数组
    var data_real = new Array(); //真实值 三维数组
    var data_pred = new Array(); //预测值 三维数组
    var data_mae = new Array();  //mae 三维数组
    var data_mape = new Array(); //mape 三维数组
    var data_rmse = new Array(); //rmse 三维数组
    var data_length = 30;       // 可视化图表中单次展示的数据长度
    var POD_TARGET = '';        // 预测的目标pod
    var MODEL_CURRENT = '';     // 当前可视化页面展示的模型
    var time_old = [];          // 上一个数据的时间，一维数组
    var update_count = [];      // 更新次数计数器
    var global_status = 0;      // 是否进行监控/更新，加载页面时默认为0

    // 初始化填充0
    for(var i = 0; i < model_types; i++) {
        data_real[MODELS[i]] = new Array();
        data_pred[MODELS[i]] = new Array();
        data_mae[MODELS[i]] = new Array();
        data_mape[MODELS[i]] = new Array();
        data_rmse[MODELS[i]] = new Array();
        time_old[MODELS[i]] = 0;
        update_count[MODELS[i]] = 0;
        data_time[MODELS[i]] = new Array();
        for(var j = 0; j < data_types_max; j++) {
            data_real[MODELS[i]][j] = new Array();
            data_pred[MODELS[i]][j] = new Array();
            data_mae[MODELS[i]][j] = new Array();
            data_mape[MODELS[i]][j] = new Array();
            data_rmse[MODELS[i]][j] = new Array();
        }
    }
    
    for(var k = 0; k < data_length; k++) {
        for(var i = 0; i < model_types; i++) {
            data_time[MODELS[i]].push(0);
            for(var j = 0; j < data_types_max; j++) {
                data_pred[MODELS[i]][j].push(0);
                data_real[MODELS[i]][j].push(0);
                data_mae[MODELS[i]][j].push(0);
                data_mape[MODELS[i]][j].push(0);
                data_rmse[MODELS[i]][j].push(0);
            }
        }       
    }

    //每个div分别创建一个form对象
    var CurrentA = new My_form("current_A", "内存占用率");
    var CurrentB = new My_form("current_B", "CPU占用率");
    var CurrentC = new My_form("current_C", "Http请求量");
    var CurrentA1 = new My_form("current_A1", "内存占用率 评价指标");
    var CurrentB1 = new My_form("current_B1", "CPU占用率 评价指标");
    var CurrentC1 = new My_form("current_C1", "Http请求量 评价指标");

    //页面加载时初始化静态图表
    CurrentA.init_static()
    CurrentB.init_static()
    CurrentC.init_static()
    CurrentA1.init_static_index()
    CurrentB1.init_static_index()
    CurrentC1.init_static_index()

    //定义form类
    function My_form(element_id, title) {

        //form类所创建在指定的div的id
        this.element_id = element_id

        //初始化图表，在具体指定元素位置创建图表，并传入数据列表
        this.init_static = function () {
            this.mychart = echarts.init(document.getElementById(this.element_id));

            // 初始化y轴数据
            var real_arr = [];
            var model_arr = [];
            for (var i = 0; i < data_length; i++) {
                real_arr.push(0);
                model_arr.push(0);
            }

            //设置图标配置项
            this.mychart.setOption({
                title: {
                    text: title,
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
                    data: ['real', 'model'],
                    textStyle: {
                        fontSize: getDpr()
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
                    data: data_time[MODELS[0]]
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    // max: 18000,
                    splitNumber: 3
                },
                series: [{
                    name: '真实值',
                    type: 'line',
                    color: "blue",
                    data: real_arr
                }, {
                    name: '模型预估值',
                    type: 'line',
                    color: "red",
                    data: model_arr
                }]
            })

        }

        this.init_static_index = function () {
            this.mychart = echarts.init(document.getElementById(this.element_id));

            // 初始化y轴数据
            var real_arr = [];
            var model_arr = [];
            for (var i = 0; i < data_length; i++) {
                real_arr.push(0);
                model_arr.push(0);
            }

            //设置图标配置项
            this.mychart.setOption({
                title: {
                    text: title,
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
                    data: ['real', 'model'],
                    textStyle: {
                        fontSize: getDpr()
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
                    data: data_time[MODELS[0]]
                },
                yAxis: {
                    type: 'value',
                    min: 0,
                    // max: 18000,
                    splitNumber: 3
                },
                series: [{
                    name: 'MAE',
                    type: 'line',
                    color: "blue",
                    data: data_mae[MODELS[0]][0]
                }, {
                    name: 'MAPE',
                    type: 'line',
                    color: "green",
                    data: data_mape[MODELS[0]][0]
                }, {
                    name: 'RMSE',
                    type: 'line',
                    color: "orange",
                    data: data_rmse[MODELS[0]][0]
                }]
            })

        }

        // 更新数据函数
        this.update_data = function (real_data, model_data, time, title) {
            this.mychart.setOption({
                title: {
                    text: title,
                    x: 'center',
                    textStyle: {
                        "fontSize": 16
                    }
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: time.slice(-data_length) // TODO
                },
                series: [{
                    name: '真实值',
                    data: real_data.slice(-data_length)
                }, {
                    name: '模型预估值',
                    data: model_data.slice(-data_length)
                }]
            });
        }

        this.update_index_data = function (mae_data, mape_data, rmse_data, title) {
            mytime = [];
            for(var i = 0; i < data_length; i++)
                mytime[i] = i;
            this.mychart.setOption({
                title: {
                    text: title,
                    x: 'center',
                    textStyle: {
                        "fontSize": 16
                    }
                },
                xAxis: {
                    type: 'category',
                    boundaryGap: false,
                    data: mytime
                },
                series: [{
                    name: 'MAE',
                    data: mae_data.slice(-data_length)
                }, {
                    name: 'MAPE',
                    data: mape_data.slice(-data_length)
                }, {
                    name: 'RMSE',
                    data: rmse_data.slice(-data_length)
                }]
            });
        }

    }

    //“开始实验”按钮点击事件
    $("button[id='start']").click(function () {
        global_status = 1;
        POD_TARGET = document.getElementById('monitor_key').value.replace(/\s+/g,"");
        MODEL_CURRENT = document.getElementById('select_model').value.replace(/\s+/g,"");
        update_all();
    })

    $("button[id='switch']").click(function () {
        global_status = 1;
        MODEL_CURRENT = document.getElementById('select_model').value.replace(/\s+/g,"");
        update_all(false);
    })

    // //“终止实验”按钮点击事件
    // $("button[id='stop']").click(function () {
    //     global_status = 0;
    //     // data_real0.fill(0);
    //     // data_real1.fill(0);
    //     // data_real2.fill(0);
    //     // data_pre0.fill(0);
    //     // data_pre1.fill(0);
    //     // data_pre2.fill(0);
    //     // data_time.fill(0)
    //     CurrentA.init_static()
    //     CurrentB.init_static()
    //     CurrentC.init_static()
    // })

    //legend字体大小
    function getDpr() {
        var windowWidth = $(window).width();
        if (windowWidth < 1920) {
            return 12
        }
        if (windowWidth >= 1920 && windowWidth <= 3840) {
            return 18
        }
        if (windowWidth > 3840 && windowWidth <= 5760) {
            return 30
        }
    };

    function cal_mae(arr1, arr2) {
        mae = 0;
        n = arr1.length;
        for(var i=0; i < arr1.length; i++) {
            mae += Math.abs(arr1[i] - arr2[i]);
            // 去掉初始填充的0
            if(arr1[i] == arr2[i])
                n-=1;
        }
        n = n > 0 ? n : 1;
        mae /= n;
        return mae;
    };

    // arr1:pred arr2:actual
    function cal_mape(arr1, arr2) {
        mape = 0;
        n = arr1.length;
        for(var i=0; i < arr1.length; i++) {
            if(arr2[i] != 0) // 去掉初始填充的0
                mape += Math.abs(arr1[i] - arr2[i]) / arr2[i];
            // 去掉初始填充的0
            if(arr1[i] == arr2[i])
                n-=1;
        }
        n = n > 0 ? n : 1;
        mape /= n;
        return mape;
    };

    function cal_rmse(arr1, arr2) {
        rmse = 0;
        n = arr1.length;
        for(var i=0; i < arr1.length; i++) {
            rmse += Math.pow(arr1[i] - arr2[i], 2);
            // 去掉初始填充的0
            if(arr1[i] == arr2[i])
                n-=1;
        }
        n = n > 0 ? n : 1;
        rmse /= n;
        rmse = Math.sqrt(rmse);
        return rmse;
    };

    // 更新预测值和真实值
    function update_real_pre(model, pod) {
        var ws = new WebSocket(config.testConfig.serverIP);
        var flag = false;
        var socket_str = ''
        if(model == 'integration')
            socket_str = pod;
        else
            socket_str = model + '_' + pod;

        ws.onopen = function() {
            console.log('连接成功');
            flag = true;
            ws.send(socket_str);
        };

        ws.onmessage = function(e){
        　　//当客户端收到服务端发来的消息时，触发onmessage事件，参数e.data包含server传递过来的数据
            data = JSON.parse(e.data)
            if(data_types == -1)
                data_types = (data.length - 1) / 2;

            // 检查时间
            if(data[0] == time_old[model]) {
                console.log('没有新数据');
                return;
            }
            else
                time_old[model] = data[0];
            update_count[model] += 1;
            

            // 更新数据
            data_time[model].push(data[0]); // 更新时间戳
            for(var i = 0; i < data_types; i++) { // 更新预测值和真实值     
                data_pred[model][i].push(data[2 * i + 1]);
                data_real[model][i].push(data[2 * i + 2]);
            }
            if(update_count[model] % data_length == 0) { // 更新指标
                for(var i = 0; i < data_types; i++) {
                    data_mae[model][i].push(cal_mae(data_pred[model][i], data_real[model][i]));
                    data_mape[model][i].push(cal_mape(data_pred[model][i], data_real[model][i]));
                    data_rmse[model][i].push(cal_rmse(data_pred[model][i], data_real[model][i]));
                }
            }         　　
        }
 
        ws.onclose = function() {
            if(flag == true) {
                s = '数据请求发送成功';
                console.log(s);
            }
            else {
                s = '数据请求发送失败，请检测网络配置';
                alert(s);
            }
        };
    }

    function update_all(flag_upd_data = true) {
        if(flag_upd_data)
            for(var i = 0; i < MODELS.length; i++) {
                update_real_pre(MODELS[i], POD_TARGET);
            }

        if (data.length == 7) {
            CurrentA.update_data(data_real[MODEL_CURRENT][0], data_pred[MODEL_CURRENT][0], data_time[MODEL_CURRENT], "内存占用率");
            CurrentB.update_data(data_real[MODEL_CURRENT][1], data_pred[MODEL_CURRENT][1], data_time[MODEL_CURRENT], "CPU占用率");
            CurrentC.update_data(data_real[MODEL_CURRENT][2], data_pred[MODEL_CURRENT][2], data_time[MODEL_CURRENT], "HTTP请求量");
            CurrentA1.update_index_data(data_mae[MODEL_CURRENT][0], data_mape[MODEL_CURRENT][0], data_rmse[MODEL_CURRENT][0], "内存占用率 评价指标");
            CurrentB1.update_index_data(data_mae[MODEL_CURRENT][1], data_mape[MODEL_CURRENT][1], data_rmse[MODEL_CURRENT][1], "CPU占用率 评价指标");
            CurrentC1.update_index_data(data_mae[MODEL_CURRENT][2], data_mape[MODEL_CURRENT][2], data_rmse[MODEL_CURRENT][2], "HTTP请求量 评价指标");
        }
        else if (data.length == 5) {
            CurrentA.update_data(data_real[MODEL_CURRENT][0], data_pred[MODEL_CURRENT][0], data_time[MODEL_CURRENT], "内存占用率");
            CurrentB.update_data(data_real[MODEL_CURRENT][1], data_pred[MODEL_CURRENT][1], data_time[MODEL_CURRENT], "CPU占用率");
            CurrentC.update_data(data_real[MODEL_CURRENT][2], data_pred[MODEL_CURRENT][2], data_time[MODEL_CURRENT], "HTTP请求量（禁用）");
            CurrentA1.update_index_data(data_mae[MODEL_CURRENT][0], data_mape[MODEL_CURRENT][0], data_rmse[MODEL_CURRENT][0], "内存占用率 评价指标");
            CurrentB1.update_index_data(data_mae[MODEL_CURRENT][1], data_mape[MODEL_CURRENT][1], data_rmse[MODEL_CURRENT][1], "CPU占用率 评价指标");
            CurrentC1.update_index_data(data_mae[MODEL_CURRENT][2], data_mape[MODEL_CURRENT][2], data_rmse[MODEL_CURRENT][2], "HTTP请求量 评价指标（禁用）");
        }
    }

    //设置监听函数每60秒更新一次
    setInterval(function () {
        if (global_status === 0) {
            return;
        }
        update_all(); 
    }, 15 * 1000);
})