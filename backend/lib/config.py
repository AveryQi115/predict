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
