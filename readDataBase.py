from influxdb import InfluxDBClient
import numpy as np
from kubernetes import client, config
import json

# 配置类
class Config:
    IP_prometheus = ''
    IP_influxdb = ''
    PORT_influxdb = 0
    USR_influxdb = ''
    PASSWD_influxdb = ''
    DB_influxdb = ''
    MONITOR_INTERVAL = 0   # 控制监控的时间间隔（秒）
    HTTP_REQUESTS_OLD = 0  # 上次监控得到的HTTP请求量，用来实现HTTP请求量的增量计算（从Web接口获取的为HTTP请求量总量）
    NUM_module = 0

    def __str__(self):
        return f"IP_prometheus {self.IP_prometheus}\nIP_influxdb {self.IP_influxdb}\nPORT_influxdb {self.PORT_influxdb}"

def read_config(path):
    """读取配置

    Args:
        path : str : 配置文件路径

    Returns:
        confObj : class Config : 配置内容
    """
    fd = open(path)
    content = fd.readlines()
    confObj = Config()
    for i in range(len(content)):
        conf = content[i].split('=')
        conf_name = conf[0].strip()
        conf_value = conf[1].strip()
        if 'IP_prometheus' == conf_name:
            confObj.IP_prometheus = conf_value
        elif 'IP_influxdb' == conf_name:
            confObj.IP_influxdb = conf_value
        elif 'PORT_influxdb' == conf_name:
            confObj.PORT_influxdb = int(conf_value)
        elif 'USR_influxdb' == conf_name:
            confObj.USR_influxdb = conf_value
        elif 'PASSWD_influxdb' == conf_name:
            confObj.PASSWD_influxdb = conf_value
        elif 'DB_influxdb' == conf_name:
            confObj.DB_influxdb = conf_value
        elif 'MONITOR_INTERVAL' == conf_name:
            confObj.MONITOR_INTERVAL = int(conf_value)
        elif 'NUM_module' == conf_name:
            confObj.NUM_module = conf_value
    fd.close()
    return(confObj)

def load_dataset(pod):
    confObj = read_config('./backend/lib/general.conf')
    try:
        client = InfluxDBClient(confObj.IP_influxdb, confObj.PORT_influxdb, confObj.USR_influxdb, confObj.PASSWD_influxdb, confObj.DB_influxdb) 
    except Exception as e:
        print(e)
        return 
    result = client.query('select * from \"' + pod + '\";')
    if result is None or len(result.raw['series'])==0 or result.raw is None:
        return None
    dataset = result.raw['series'][0]['values']
    return dataset

def read_cluster():
    usage_data = {}
    for node,pods in {
        "vm-4c8g-node2":[
            "buyservice-67dc97d8c6-tcslv",
            "influxdb-776b79db44-g668h",
            "storageservice-77566757c9-7lpvq",
            "timeservice-6d49cb4875-z6m6q",
            "webapp-d5585d547-kzqn8"
        ],
        "vm-4c8g-node3":[
            "storageservice-1-588769c495-c4fzn",
            "tableservice-7554b56f68-4n55v"
        ]}.items():
        print(node,pods)
        usage_data[node] = []
        for pod in pods:
            data = load_dataset(pod)
            if data is None:
                print(pod)
                continue
            usage_data[node].append({
                "pod_name"  : pod,
                "data"      : data
            })
            print(node,pod,len(data))
    with open('monitor_data.json','w')as f:
        json.dump(usage_data,f)
    return

if __name__=="__main__":
    read_cluster()
