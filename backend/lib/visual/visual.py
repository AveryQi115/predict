from influxdb import InfluxDBClient
from utils import write_log
from config import read_config
import time
import numpy as np

LOG_PATH = 'lib/visual/visual.log'
CONFIG_PATH = 'lib/general.conf'

# load_data每调用一次只返回最新的数据
def load_monitor_data(pod, _):
    confObj = read_config(CONFIG_PATH)
    # 从influxdb读取负载数据
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[load_monitor_data.{pod}] '+ str(e), LOG_PATH)
        return None
    result = client.query('select * from \"' + pod + '\";')
    if len(result.raw['series'])<=0:
        return None
    dataset = result.raw['series'][0]['values']
    latest_data = dataset[-1]
    timeArray = time.strptime(latest_data[0],'%Y-%m-%dT%H:%M:%S.%fZ')
    latest_data[0] = time.mktime(timeArray)
    return latest_data

def load_predict_data(pod, predict_model):
    confObj = read_config(CONFIG_PATH)
    # 从influxdb读取负载数据
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[load_predict_data.{pod}.{predict_model}] '+ str(e), LOG_PATH)
        return 
    result = client.query('select * from \"pred_' + pod + '_' + predict_model + '\";') # TODO: 前缀变了
    try:
        points = list(result.get_points())
        point = points[-1]
        timeArray = time.strptime(point["time"],'%Y-%m-%dT%H:%M:%S.%fZ')
        mem_pred = point["var0_mem_usage_rate_pred"]
        cpu_pred = point["var1_cpu_usage_rate_pred"]
        mem_real = point["var0_mem_usage_rate_real"]
        cpu_real = point["var1_cpu_usage_rate_real"]
        return [time.mktime(timeArray), mem_real,mem_pred,cpu_real,cpu_pred]
    except Exception as e:
        print(f'[load_predict_data.{pod}.{predict_model}] 数据库中查询不到预测数据，请等待片刻或检查预测任务是否发送成功')

# 从influxdb读取负载数据
def load_dataset(pod):
    confObj = read_config(CONFIG_PATH)
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[load_dataset.{pod}] '+str(e), LOG_PATH)
        return 
    result = client.query('select * from \"' + pod + '\";') 
    dataset = result.raw['series'][0]['values']
    return np.array(dataset)

# 为动态部署服务读取一个命名空间下所有pods
# pods为pod名称的list
# TODO: 改进成latest_data
def load_dataset_for_namespaced_pods(pods):
    confObj = read_config(CONFIG_PATH)
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        write_log('error', f'[load_dataset.namespaced_pods] '+str(e), LOG_PATH)
        return 
    res = {}
    for pod in pods:
        result = client.query('select * from \"' + pod + '\";') 
        dataset = result.raw['series'][0]['values']
        res[pod] = dataset
    return res