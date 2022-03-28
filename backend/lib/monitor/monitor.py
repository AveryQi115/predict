import requests, json, time
import inspect
import ctypes
from influxdb import InfluxDBClient
from config import read_config
from utils import write_log, clearInfluxDB, writeMonitorDataToInfluxDB
import _thread

# 配置文件路径声明
CONFIG_PATH = 'lib/general.conf'
LOG_PATH = 'lib/monitor/monitor.log'

FLAG_CLEARDB = False   # 布尔变量，决定监控线程在启动时是否清空数据库（建议清空，否则会导致监控数据在时间上不连续）

def queryProme(expr, confObj):
    """prometheus web查询接口

    Args:
        expr : str : prometheus查询正则表达式
        address : str : prometheus server访问地址

    Returns:
        http返回json数据   
    """
    url = confObj.IP_prometheus + '/api/v1/query?query=' + expr
    try:
        return json.loads(requests.get(url=url).content.decode('utf8', 'ignore'))
    except Exception as e:
        write_log('error', f'[queryProme] expr={expr} '+str(e), LOG_PATH)
        return 

def queryHttpRequestsNum(confObj, pod_ip):
    """从自建API查询http请求量

    Args:
        confObj : class Config : 配置类
        pod_ip : str : pod的ip，此pod必须为自行修改且支持HTTP请求监控的webApp

    HTTP请求说明:
        url : http://[pod_ip]/httpwork.php?method=monitor
        ret : "http_requests_total [http请求量/int]"  注：双引号内为HTTP请求接收内容

    Returns: 
        res : int : http请求总量
    """
    url = 'http://' + pod_ip + '/httpwork.php?method=monitor'
    try:
        res = requests.get(url=url).content.decode('utf8', 'ignore')
        res = res.split()
        return int(res[1])
    except Exception as e:
        write_log('error', f'[queryHttpRequestsNum] pod_ip={pod_ip} '+str(e), LOG_PATH)
        return   

def data_collection(pod_name, confObj, option):
    """收集指定pod在当前时刻的负载数据
    
    Args: 
        pod_name
        confObj
        pod_ip
        option : str : 决定是否监控请求数据，若option为空字符串，则不监控请求数据
    """

    # 1 记录实时数据
    # WARNING: 若要将数据修改为使用率，则POD在创建时必须声明LIMIT值，否则将无法查询到结果！！！
    # 1.1 查询memory数据(实时)
    mem_data = []
    MyQuery = 'avg((avg (container_memory_working_set_bytes{pod="'+ pod_name + '"}) by (container_name , pod ))/ on (container_name , pod)(avg (container_spec_memory_limit_bytes>0 ) by (container_name, pod)))'
    result_json = queryProme(MyQuery, confObj)
    if result_json is None:
        pass
    else:
        result_data = result_json['data']['result']
        write_log('INFO', f'mem result data: {result_data}', LOG_PATH)
        for i in range(len(result_data)):
            if 'container' in result_data[i]['metric']: #这条数据为pod中容器的数据
                pass
            else: #这条数据为pod数据
                mem_data = result_data[i]['value']
                write_log('INFO', f'mem_data: {mem_data}', LOG_PATH)

    # 1.2 查询cpu数据(实时) 
    cpu_data = []
    MyQuery = 'sum(rate(container_cpu_usage_seconds_total{pod="' + pod_name + '"}[1m]))'
    result_json = queryProme(MyQuery, confObj)
    if result_json is None:
        cpu_data = []
    else:
        result_data = result_json['data']['result']
        for i in range(len(result_data)):
            if 'container' in result_data[i]['metric']: #这条数据为pod中容器的数据
                pass
            else: #这条数据为pod数据
                cpu_data = result_data[i]['value']
                write_log('INFO', f'cpu_data: {cpu_data}', LOG_PATH)

    # # 1.3 查询http请求增量数据(实时)
    # if option == "":
    #     http_data = int(queryHttpRequestsNum(confObj, pod_ip))
    #     # 修改为增量
    #     if confObj.HTTP_REQUESTS_OLD == 0: # 第一次默认增量为0
    #         confObj.HTTP_REQUESTS_OLD = http_data
    #         http_data = 0
    #     else:
    #         temp = http_data
    #         http_data = http_data - confObj.HTTP_REQUESTS_OLD - 1 # 去掉查询的那次请求
    #         confObj.HTTP_REQUESTS_OLD = temp 

    # 1.4 将数据进行合并并输出到数据库 [内存占用率，CPU占用率，HTTP请求增量]
    if len(cpu_data) > 1 and len(mem_data) > 1: # 进行安全检查
        try:
            csv_data = [float(mem_data[1]), float(cpu_data[1])]

            # 结果输出到时序数据库(实时)
            writeMonitorDataToInfluxDB(csv_data, pod_name, confObj, LOG_PATH)
        except Exception as e:
            print(e)
            return
    else:
        write_log('error', f'[data_collection.{pod_name}] CPU或内存数据缺失, cpu_data={cpu_data}, mem_data={mem_data}',LOG_PATH)

def monitor_thread(pod_name, startTime, option):
    """监测线程函数
    
    Args: 
        pod_name
        time
        option
        以上均为传递参数
    """
    # 写日志
    write_log('INFO', 'monitoring ' + pod_name, LOG_PATH)

    # 读取配置
    confObj = read_config(CONFIG_PATH)

    # 清空数据库
    if FLAG_CLEARDB is True:
        clearInfluxDB(pod_name, confObj)

    # 进行监控
    while True: 
        print('monitor ' + pod_name)
        data_collection(pod_name=pod_name, confObj=confObj, option=option)
        time.sleep(confObj.MONITOR_INTERVAL)

def monitor_pods(pod_names, cleardb=None):
    monitor_pod_threads = []
    if cleardb is not None:
        FLAG_CLEARDB = True
    for pod_name in pod_names:
        t_id = _thread.start_new_thread(monitor_thread, (pod_name, 0, ""))
        t_pod = pod_name
        monitor_pod_threads.append([t_id, t_pod])
    return monitor_pod_threads

# # 终止子线程
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
