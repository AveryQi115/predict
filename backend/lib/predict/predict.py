# 数据处理库
import numpy as np

# 机器学习库
from sklearn.linear_model import PassiveAggressiveRegressor
from keras.models import load_model
import joblib

# 其他库
import math
import os
import time
os.environ["CUDA_VISIBLE_DEVICES"]="-1"   

# 自己编写的库
from utils import write_log, clearInfluxDB, read_pod_config, write_pod_config
from visual import load_dataset
from config import read_config
from utils import writePredictDataToInfluxDB

# 固定配置变量
PREDICT_INTERVAL = 15

# 配置文件路径声明
CONFIG_PATH = 'lib/general.conf'
LOG_PATH = 'lib/predict/predict.log'


def train_model_integration(model, pod_name, VAR_NUM, confObj):
    look_back = 3
    update_window = 3
    wm_window = 3 # 模型间权重更新窗口
    beta1= 0.5  # 源域与目标域模型权重衰减因子
    beta2= 0.5  # 各源域模型的权重衰减因子
    beta3= 0.2  # 源域各基础模型的权重衰减因子


    # 构建PA模型（在线学习）
    pa = PassiveAggressiveRegressor(max_iter=10, random_state=0,tol=1e-3, shuffle=False, loss='squared_epsilon_insensitive', epsilon=0.01)  

    MODELS_source = ['rf', 'svr', 'lstm']
    # TODO: hard code
    pods_source = ['buyservice-6978f578df-6svnq', 'partservice-694977484-9mrjd', 'storageservice-6d84b5fbc4-sq7n2', 'tableservice-747994cfd5-8cpl7', 'timeservice-8d66c56b-kf8r5']

    # 构建预测权重向量
    # 预测权重向量分为三种：（1）源域与目标域间的权重（2）各源域间的权重（3）源域内各模型间的权重
    # 在此之上，对于每个待预测变量，都有一组预测权重向量
    w_st = [] # 源域与目标域间的权重
    w_s = []  # 各源域间的权重
    w_m = []  # 源域内各模型间的权重
    for i in range(VAR_NUM): # 对于每个变量
        w_st.append([0.5,0.5])
        w_s.append([1/len(pods_source)] * len(pods_source))
        temp = []
        for j in range(len(pods_source)): # 对于每个源域
            temp.append([1/len(MODELS_source)] * len(MODELS_source))
        w_m.append(temp)

    # 进行预测  
    count = 0
    data_num_old = 0

    res_final_old = []
    res_st_old = []
    res_s_old = []
    res_m_old = []
    err_m_queue = []

    pod_conf_path = './async/' + pod_name + '.conf'
    pod_conf = read_pod_config(pod_conf_path)
    if pod_conf.count != 0:
        data_num_old = pod_conf.index - 1
        pod_conf.count -= 1
        pod_conf.checked = True
        write_pod_config(pod_conf_path, pod_conf)
        
    while True:
        res_final = np.zeros((VAR_NUM))                                        # 最终的预测值
        res_st = np.zeros((VAR_NUM,2))                                         # 源域与目标域的预测值
        res_s = np.zeros((VAR_NUM,len(pods_source)))                           # 各源域的预测值
        res_m = np.zeros((VAR_NUM,len(pods_source), len(MODELS_source)))       # 源域模型的预测值

        # 获取最新look_back长度负载数据
        latest_data = load_dataset(pod_name, confObj)
        data_num = len(latest_data)

        # 更新async文件
        if pod_conf.checked == False:
            pod_conf.checked = True
            pod_conf.index = data_num
            pod_conf.count = confObj.NUM_module
            write_pod_config(pod_conf_path, pod_conf)

        if data_num_old == 0: # 初始情况
            data_num_old = data_num       
        elif data_num <= data_num_old: # 没有新数据
            time.sleep(1)
            continue
        else: # 有新数据，进行截断
            latest_data = latest_data[:data_num_old+1]
            data_num_old += 1

        # 进行预测(源域模型)
        predict_X = latest_data[-look_back:, 1:].astype('float64')
        predict_X_lstm = predict_X.reshape([1,look_back,VAR_NUM])
        for i in range(VAR_NUM): # 对于每个待预测变量
            for j in range(len(pods_source)): # 对于每个源域
                for k in range(len(MODELS_source)): # 对于源域中每个模型
                    if MODELS_source[k] == 'lstm':
                        batch_size = 1
                        res_m[i][j][k] = model[i][j][k].predict(predict_X_lstm[:,:,(i,)], batch_size)[0]
                    else:
                        res_m[i][j][k] = model[i][j][k].predict([predict_X[:,i]])[0]

        # 进行预测(在线学习模型)
        if count == 0:
            for i in range(VAR_NUM):
                res_st[i][1] = 0
        else:
            for i in range(VAR_NUM):
                res_st[i][1] = pa.predict([predict_X[:,i]])[0]
        
        # 构建预测结果
        for i in range(VAR_NUM): # 对于每个待预测变量
            res_final[i] += w_st[i][1] * res_st[i][1]
            for j in range(len(pods_source)): # 对于每个源域
                for k in range(len(MODELS_source)): # 对于源域中每个模型
                    res_s[i][j] += w_m[i][j][k] * res_m[i][j][k]
                res_st[i][0] += w_s[i][j] * res_s[i][j]
            res_final[i] += w_st[i][0] * res_st[i][0]

        # 更新模型
        if len(latest_data) > look_back:
            if len(latest_data) - look_back < update_window:
                window_size = len(latest_data) - look_back
            else:
                window_size = update_window
            for i in range(VAR_NUM): # 对于每个预测变量
                train_Xi = []
                train_Yi = []
                for k in range(window_size):
                    train_Xi.append(latest_data[-look_back-1-window_size+1+k:-window_size+k, i+1])
                    train_Yi.append(latest_data[-window_size+k, i+1])
                train_Xi = np.array(train_Xi).astype('float64')
                train_Yi = np.array(train_Yi).astype('float64')
                for j in range(len(pods_source)): # 对于每个源域
                    for k in range(len(MODELS_source)): # 对于源域中每个模型
                        if MODELS_source[k] == 'lstm':
                            model[i][j][k].fit(train_Xi.reshape([window_size,look_back,1]), train_Yi)
                        else:
                            model[i][j][k].fit(train_Xi, train_Yi)
                pa.fit(train_Xi, train_Yi)

        # 更新权重
        if count == 0: # 第一次不更新权重
            pass
        else:
            # 计算误差
            err_st = np.zeros((VAR_NUM,2))                                         # 源域与目标域的预测值
            err_s = np.zeros((VAR_NUM,len(pods_source)))                           # 各源域的预测值
            err_m = np.zeros((VAR_NUM, len(pods_source), len(MODELS_source)))      # 源域模型的预测值
            for i in range(VAR_NUM): # 对于每个待预测变量
                real = predict_X[-1][i]
                err_st[i][0] = math.fabs(real - res_st_old[i][0])
                err_st[i][1] = math.fabs(real - res_st_old[i][1])
                for j in range(len(pods_source)): # 对于每个源域
                    err_s[i][j] = math.fabs(real - res_s_old[i][j])
                    for k in range(len(MODELS_source)): # 对于源域中每个模型
                        err_m[i][j][k] = math.fabs(real - res_m_old[i][j][k])
            
            err_m_queue.append(err_m)
            if len(err_m_queue) > wm_window:
                err_m_queue.pop(0)

            # 更新权重 
            for i in range(VAR_NUM): # 对于每个待预测变量
                # 更新源域与目标域
                if err_st[i][0] > err_st[i][1]:
                    w_st[i][0] *= beta1
                    total = w_st[i][0] + w_st[i][1]
                    w_st[i][0] /= total
                    w_st[i][1] /= total
                elif err_st[i][0] < err_st[i][1]:
                    w_st[i][1] *= beta1
                    total = w_st[i][0] + w_st[i][1]
                    w_st[i][0] /= total
                    w_st[i][1] /= total

                # 更新源域间
                if len(pods_source) > 1:
                    error_index = np.argsort(err_s[i]) #返回从小到大值对应索引的排序
                    sign_s = 0
                    sum_s = 0
                    for s in error_index:
                        w_s[i][s] = w_s[i][s] * beta2 ** sign_s
                        sum_s += w_s[i][s]
                        sign_s += 1
                    for s in range(len(pods_source)):
                        w_s[i][s] /= sum_s

                # 更新源域内模型间
                for j in range(len(pods_source)): # 对于每个源域  
                    sum_m = 0
                    for m in range(len(MODELS_source)):
                        err_m_avg = 0
                        for k in range(len(err_m_queue)):
                            err_m_avg += err_m_queue[k][i][j][m]
                        err_m_avg /= len(err_m_queue)
                        w_m[i][j][m] = 1 / err_m_avg
                        sum_m += w_m[i][j][m]
                    for m in range(len(MODELS_source)):
                        w_m[i][j][m] /= sum_m

        # 组织数据写入influxdb
        if count != 0:
            writePredictDataToInfluxDB(latest_data[-1], res_final_old, pod_name, 'integration', confObj, LOG_PATH)

        # 睡眠
        count += 1
        res_final_old = np.copy(res_final)
        res_m_old = np.copy(res_m)
        res_s_old = np.copy(res_s)
        res_st_old = np.copy(res_st)
        print('predict integration' + pod_name)
        time.sleep(PREDICT_INTERVAL)

def train_model_rf(model, pod_name, VAR_NUM, confObj):
    look_back = 3
    update_window = 3

    # 进行预测  
    count = 0
    data_num_old = 0
    res_final_old = []

    pod_conf_path = './async/' + pod_name + '.conf'
    pod_conf = read_pod_config(pod_conf_path)
    if pod_conf.count != 0:
        data_num_old = pod_conf.index - 1
        pod_conf.count -= 1
        pod_conf.checked = True
        write_pod_config(pod_conf_path, pod_conf)

    while True:
        res_final = np.zeros((VAR_NUM))      # 最终的预测值

        # 获取最新look_back长度负载数据
        latest_data = load_dataset(pod_name, confObj)
        data_num = len(latest_data)

        # 更新async文件
        if pod_conf.checked == False:
            pod_conf.checked = True
            pod_conf.index = data_num
            pod_conf.count = confObj.NUM_module
            write_pod_config(pod_conf_path, pod_conf)

        if data_num_old == 0: # 初始情况
            data_num_old = len(latest_data)
        elif data_num <= data_num_old: # 没有新数据
            time.sleep(1)
            continue
        else: # 有新数据，进行截断
            latest_data = latest_data[:data_num_old+1]
            data_num_old += 1

        # 进行预测
        predict_X = latest_data[-look_back:, 1:].astype('float64')
        for i in range(VAR_NUM): # 对于每个待预测变量
            res_final[i] = model[i].predict([predict_X[:,i]])[0]

        # 更新模型
        if len(latest_data) > look_back:
            if len(latest_data) - look_back < update_window:
                window_size = len(latest_data) - look_back
            else:
                window_size = update_window
            for i in range(VAR_NUM): # 对于每个预测变量
                train_Xi = []
                train_Yi = []
                for k in range(window_size):
                    train_Xi.append(latest_data[-look_back-1-window_size+1+k:-window_size+k, i+1])
                    train_Yi.append(latest_data[-window_size+k, i+1])
                train_Xi = np.array(train_Xi).astype('float64')
                train_Yi = np.array(train_Yi).astype('float64')
                model[i].fit(train_Xi, train_Yi)

        # 组织数据写入influxdb
        if count != 0:
            writePredictDataToInfluxDB(latest_data[-1], res_final_old, pod_name, 'rf', confObj, LOG_PATH)

        # 睡眠
        count += 1
        res_final_old = np.copy(res_final)
        print('predict rf ' + pod_name)
        time.sleep(PREDICT_INTERVAL)

def train_model_svr(model, pod_name, VAR_NUM, confObj):
    look_back = 3
    update_window = 3

    # 进行预测  
    count = 0
    data_num_old = 0
    res_final_old = []

    pod_conf_path = './async/' + pod_name + '.conf'
    pod_conf = read_pod_config(pod_conf_path)
    if pod_conf.count != 0:
        data_num_old = pod_conf.index - 1
        pod_conf.count -= 1
        pod_conf.checked = True
        write_pod_config(pod_conf_path, pod_conf)

    while True:
        res_final = np.zeros((VAR_NUM))      # 最终的预测值

        # 获取最新look_back长度负载数据
        latest_data = load_dataset(pod_name, confObj)
        data_num = len(latest_data)

        # 更新async文件
        if pod_conf.checked == False:
            pod_conf.checked = True
            pod_conf.index = data_num
            pod_conf.count = confObj.NUM_module
            write_pod_config(pod_conf_path, pod_conf)

        if data_num_old == 0: # 初始情况
            data_num_old = len(latest_data)
        elif data_num <= data_num_old: # 没有新数据
            time.sleep(1)
            continue
        else: # 有新数据，进行截断
            latest_data = latest_data[:data_num_old+1]
            data_num_old += 1

        # 进行预测
        predict_X = latest_data[-look_back:, 1:].astype('float64')
        for i in range(VAR_NUM): # 对于每个待预测变量
            res_final[i] = model[i].predict([predict_X[:,i]])[0]

        # 更新模型
        if len(latest_data) > look_back:
            if len(latest_data) - look_back < update_window:
                window_size = len(latest_data) - look_back
            else:
                window_size = update_window
            for i in range(VAR_NUM): # 对于每个预测变量
                train_Xi = []
                train_Yi = []
                for k in range(window_size):
                    train_Xi.append(latest_data[-look_back-1-window_size+1+k:-window_size+k, i+1])
                    train_Yi.append(latest_data[-window_size+k, i+1])
                train_Xi = np.array(train_Xi).astype('float64')
                train_Yi = np.array(train_Yi).astype('float64')
                model[i].fit(train_Xi, train_Yi)

        # 组织数据写入influxdb
        if count != 0:
            writePredictDataToInfluxDB(latest_data[-1], res_final_old, pod_name, 'svr', confObj, LOG_PATH)

        # 睡眠
        count += 1
        res_final_old = np.copy(res_final)
        print('predict svr ' + pod_name)
        time.sleep(PREDICT_INTERVAL)

def train_model_lstm(model, pod_name, VAR_NUM, confObj):
    look_back = 3
    update_window = 3

    # 进行预测  
    count = 0
    res_final_old = []
    data_num_old = 0

    pod_conf_path = './async/' + pod_name + '.conf'
    pod_conf = read_pod_config(pod_conf_path)
    if pod_conf.count != 0:
        data_num_old = pod_conf.index - 1
        pod_conf.count -= 1
        pod_conf.checked = True
        write_pod_config(pod_conf_path, pod_conf)

    while True:
        res_final = np.zeros((VAR_NUM))      # 最终的预测值

        # 获取最新look_back长度负载数据
        latest_data = load_dataset(pod_name)
        data_num = len(latest_data)
        print(f'[train_model_lstm] data_num = {data_num} latest_data.shape = {latest_data.shape}\n\n\n')

        # 更新async文件
        if pod_conf.checked == False:
            pod_conf.checked = True
            pod_conf.index = data_num
            pod_conf.count = confObj.NUM_module             #TODO: confObj没有NUM_module属性
            write_pod_config(pod_conf_path, pod_conf)

        if data_num_old == 0: # 初始情况
            data_num_old = len(latest_data)
        elif data_num <= data_num_old: # 没有新数据
            time.sleep(1)
            continue
        else: # 有新数据，进行截断
            latest_data = latest_data[:data_num_old+1]
            data_num_old += 1

        if len(latest_data) < look_back: # 检查数据是否充足
            time.sleep(PREDICT_INTERVAL) 
            continue

        # 进行预测
        predict_X = latest_data[-look_back:, 1:].astype('float64')
        predict_X = predict_X.reshape([1,look_back,VAR_NUM])
        batch_size = 1
        for i in range(VAR_NUM): # 对于每个待预测变量
            predict_Xi = predict_X[:,:,(i,)]
            res_final[i] = model[i].predict(predict_Xi, batch_size)[0]

        # 更新模型
        if len(latest_data) > look_back:
            if len(latest_data) - look_back < update_window:
                window_size = len(latest_data) - look_back
            else:
                window_size = update_window
            for i in range(VAR_NUM): # 对于每个预测变量
                train_Xi = []
                train_Yi = []
                for k in range(window_size):
                    train_Xi.append(latest_data[-look_back-window_size+k:-window_size+k, i+1])
                    train_Yi.append(latest_data[-window_size+k, i+1])
                train_Xi = np.array(train_Xi).astype('float64')
                train_Yi = np.array(train_Yi).astype('float64')
                model[i].fit(train_Xi.reshape([window_size,look_back,1]), train_Yi)

        # 组织数据写入influxdb
        if count != 0:
            writePredictDataToInfluxDB(latest_data[-1], res_final_old, pod_name, 'lstm', confObj, LOG_PATH)
            print(latest_data[-1],res_final_old)
            yield (latest_data[-1].shape,res_final_old.shape)

        # 睡眠
        count += 1
        res_final_old = np.copy(res_final)
        time.sleep(PREDICT_INTERVAL)

def load_model_arrays(pod_name, predict_model,VAR_NUM):
    model = []
    MODELS_source = ['rf', 'svr', 'lstm']
    # TODO: hard code
    pods_source = ['buyservice-6978f578df-6svnq', 'partservice-694977484-9mrjd', 'storageservice-6d84b5fbc4-sq7n2', 'tableservice-747994cfd5-8cpl7', 'timeservice-8d66c56b-kf8r5']
    if(predict_model=='integration'):
        for i in  range(VAR_NUM): # 对于每个变量
            modeli = []
            for j in range(len(pods_source)): # 对于每个源域
                modelj = []
                for k in range(len(MODELS_source)): # 对于每个源域模型
                    try:
                        if MODELS_source[k] == 'lstm':
                            model_name = 'models/var' + str(i) + '.' + pods_source[j] + '.' + MODELS_source[k]  + '.h5'
                            modelj.append(load_model(model_name))
                        else:
                            model_name = 'models/var' + str(i) + '.' + pods_source[j] + '.' + MODELS_source[k]  + '.model'
                            modelj.append(joblib.load(model_name))
                    except Exception as e:
                        write_log('error', str(e), LOG_PATH)
                        return
                modeli.append(modelj)    
            model.append(modeli)
    else:
        for i in range(VAR_NUM): # 对于每个变量
            if predict_model=='lstm':
                model_name = 'models/var' + str(i) + '.' + pod_name + '.' + predict_model  + '.h5'
                print(model_name)
                modeli = load_model(model_name)
            else:
                model_name = 'models/var' + str(i) + '.' + pod_name + '.' + predict_model  + '.model'
                modeli = load_model(model_name)
            model.append(modeli) 
    return model

def OT(pod_name,predict_model):
    write_log('INFO', f'[predict_thread.{pod_name}.{predict_model}] start predict thread', LOG_PATH)
    confObj = read_config(CONFIG_PATH)
    # 清空数据库
    clearInfluxDB(f'pred_{pod_name}_{predict_model}', confObj)
    
    # 读取变量个数
    res = load_dataset(pod_name)
    VAR_NUM = len(res[-1]) - 1
    write_log('INFO', f'[OT.{pod_name}.{predict_model}] VAR_NUM = {VAR_NUM}, res.shape={res.shape}', LOG_PATH)

    # 加载模型
    model = load_model_arrays(pod_name,predict_model,VAR_NUM)
    train_model = None
    if predict_model=='integration':
        train_model = train_model_integration
    elif predict_model=='lstm':
        train_model = train_model_lstm
    elif predict_model=='svr':
        train_model = train_model_svr
    elif predict_model=='rf':
        train_model = train_model_rf

    for latest_data_shape, res_final_shape in train_model(model, pod_name, VAR_NUM, confObj):
        print(latest_data_shape)
        print(res_final_shape)
        yield (latest_data_shape,res_final_shape)
    