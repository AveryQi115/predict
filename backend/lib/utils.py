import time, datetime
from influxdb import InfluxDBClient

def write_log(type, content, log_path):
    """写日志

    Args:
        type : str : 可自行定义的日志条目种类，如info、error等
        content : str : 日志的内容

    Returns:
        无
    """
    fd = open(log_path, 'a')
    fd.write('[' + type + '] ' + time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())  + content + '\n')
    fd.close()

def clearInfluxDB(pod_name, confObj):
    """清空数据库中对指定pod原有的监控数据

    Args:
        pod_name : str : 监控pod名
        confObj : class Config : 配置类
    """
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[clearInflucDB] pod_name={pod_name} '+ str(e), LOG_PATH)
        return 

    # 删表
    client.drop_measurement(pod_name)

def writeMonitorDataToInfluxDB(data, pod_name, confObj, LOG_PATH):
    """将结果写入influxdb

    Args:
        data : list : 数据
        pod_name : str : 监控pod名
        confObj : class Config : 配置类
    """
    # 创建Client
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[writeToInflucDB] create client failed, data={data}, pod_name={pod_name} '+ str(e), LOG_PATH)
        return 

    # 向数据库写入数据
    current_time = datetime.datetime.utcnow().isoformat("T")
    new_json = []

    if(len(data) == 3): # 写入HTTP请求数据
        new_json = [
            {
                "measurement": pod_name,
                "time": current_time,
                "tags": {},
                "fields": {
                    "var0_mem_usage_rate": float(data[0]),
                    "var1_cpu_usage_rate": float(data[1]),
                    "var2_http_requests" : int(data[2])
                },
            }
        ]
    elif(len(data) == 2): # 不写入HTTP请求数据
        new_json = [
            {
                "measurement": pod_name,
                "time": current_time,
                "tags": {},
                "fields": {
                    "var0_mem_usage_rate": float(data[0]),
                    "var1_cpu_usage_rate": float(data[1]),
                },
            }
        ]

    # 写入数据
    try:
        res = client.write_points(new_json)
    except Exception as e:
        write_log('error', f'[writeToInflucDB] write data failed, data={data}, pod_name={pod_name} '+ str(e), LOG_PATH)
        return

def writePredictDataToInfluxDB(data_real, data_pred, pod_name, predict_model, confObj, LOG_PATH):
    """将预测结果写入influxdb

    Args:
        data_real:list:真实值([时间戳，数据项1，数据项2，...])
        data_pred:list:预测值([数据项1，数据项2，...])
        pod_name
        confObj
        dbname_ext:str:数据库中表的命名的拓展字符串，决定表的命名
    """
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('[writePredictDataToInfluxDB] error', str(e), LOG_PATH)
        return 

    # 向数据库写入数据
    new_json = []
    if len(data_real) == 4: # 包含http请求预测
        new_json = [
            {
                "measurement": 'pred_' + pod_name + '_' + predict_model,
                "time": data_real[0],
                "tags": {},
                "fields": {
                    "var0_mem_usage_rate_pred": float(data_pred[0]),
                    "var1_cpu_usage_rate_pred": float(data_pred[1]),
                    "var2_http_requests_pred" : int(data_pred[2]),
                    "var0_mem_usage_rate_real": float(data_real[1]),
                    "var1_cpu_usage_rate_real": float(data_real[2]),
                    "var2_http_requests_real" : int(data_real[3])
                },
            }
        ]
    elif len(data_real) == 3: # 不包含http请求预测
        new_json = [
            {
                "measurement": 'pred_' + pod_name + '_' + predict_model,
                "time": data_real[0],
                "tags": {},
                "fields": {
                    "var0_mem_usage_rate_pred": float(data_pred[0]),
                    "var1_cpu_usage_rate_pred": float(data_pred[1]),
                    "var0_mem_usage_rate_real": float(data_real[1]),
                    "var1_cpu_usage_rate_real": float(data_real[2]),
                },
            }
        ]
    try:
        res = client.write_points(new_json)
    except Exception as e:
        write_log('[writePredictDataToInfluxDB] error', str(e), LOG_PATH)
        return


# 此类用于不同预测模块间起始位置的同步
class Config_pod:
    pod_name = ''
    count = 0
    index = 0
    checked = False

# 读取预测模块同步文件
def read_pod_config(path):
    confObj = Config_pod()
    try:
        fd = open(path, 'r')
    except Exception as e:
        return confObj
    content = fd.readlines()
    for i in range(len(content)):
        conf = content[i].split('=')
        conf_name = conf[0].strip()
        conf_value = conf[1].strip()
        if 'count' == conf_name:
            confObj.count = int(conf_value)
        elif 'index' == conf_name:
            confObj.index = int(conf_value)
    fd.close()
    return confObj

# 写入预测模块同步文件
def write_pod_config(path, conf):
    fd = open(path, 'w')
    content = 'count = ' + str(conf.count) + '\n' + 'index = ' + str(conf.index) + '\n'
    fd.write(content)
    fd.close()
    return

def podnames_to_deploymentnames(pod_names, pod_deployment_mappings):
    deployment_names = []
    for pod_name in pod_names:
        deployment_names.append(pod_deployment_mappings[pod_name])
    return deployment_names

def nodepodmappings_to_nodedeploymentmappings(node_pod_mappings,pod_deployment_mappings):
    node_deployment_mappings = {}
    for node, pod_names in node_pod_mappings.items():
        node_deployment_mappings[node] = []
        for pod_name in pod_names:
            node_deployment_mappings[node].append(pod_deployment_mappings[pod_name])
    return node_deployment_mappings

def poddata_to_deploymentdata(raw_data, pod_deployment_mappings):
    deployment_raw_data = {}
    for pod_name, pod_data in raw_data.items():
        deployment_raw_data[pod_deployment_mappings[pod_name]] = pod_data
    return deployment_raw_data