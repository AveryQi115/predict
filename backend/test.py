from flask import Flask, request, jsonify, json
from flask_cors import CORS
from flask_socketio import SocketIO, send
import _thread
import sys
import time
sys.path.append( "lib" )
sys.path.append( "lib/monitor" )
sys.path.append( "lib/client" )
sys.path.append( "lib/predict" )
sys.path.append( "lib/visual" )
sys.path.append( "lib/deploy")
from monitor import monitor_thread, _async_raise, monitor_pods, queryOnce
from k8sclient import Config, getPods, getDeployments, getServices, getNodes, getPodNamesForNamespace, getNodeNamesForNamespace, getMappingsForNamespace, handleMigrationAction
from visual import load_monitor_data, load_predict_data, load_dataset_for_namespaced_pods
from predict import OT
from deploy import load_model, NODE_NUM, POD_NUM, State
from utils import podnames_to_deploymentnames, nodepodmappings_to_nodedeploymentmappings, poddata_to_deploymentdata
from copy import copy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

Cors = CORS(app)
CORS(app, resources={r'/*': {'origins': '*'}},CORS_SUPPORTS_CREDENTIALS = True)

socketio = SocketIO(app, cors_allowed_origins="*")

# 全局thread列表，用来控制thread的停止
QUEST_ARRAY = []
sending_data_threads = {}
deploy_th = None

@app.route('/nodes')
def Nodes():
    config = Config()
    nodes = getNodes(config)
    return jsonify({
        "nodes": nodes,
    })
    
@app.route('/deployments')
def Deployments():
    config = Config()
    deployments = getDeployments(config)
    return jsonify({
                    "deployments"   : deployments,
                    })

def addStatusProp(pods):
    pods_with_status = []
    for pod in pods:
        pod["monitored"] = False
        for T in QUEST_ARRAY:
            if pod["name"] == T[1]:
                pod["monitored"] = True
        pods_with_status.append(pod)
    return pods_with_status

@app.route('/pods', methods = ['POST', 'GET'])
def Pods():
    print(request.method)
    if request.method=='GET':
        config = Config()
        pods = getPods(config)
        pods_with_status = addStatusProp(pods)
        return jsonify({
                        "pods"   : pods_with_status,
                        })
    elif request.method=='POST':
        data = json.loads(request.data)
        pods = data["SelectedPods"]
        time = data["StartTime"]
        option = data["option"]
        if option == 'monitor':
            for pod in pods:
                # 启动监控线程
                try:
                    t_id = _thread.start_new_thread(monitor_thread, (pod['name'], time, option))
                    t_pod = pod['name']
                    QUEST_ARRAY.append([t_id, t_pod])
                except:
                    print(f"[Pods.Post] create monitor thread failed, pod={pod['name']}, time={time}, option=monitor")
            return jsonify({
                "msg"       : f"[Pod.Post] create monitor threads done",
                "result"    : 0,
            })
        elif option == 'stop':
            QUEST_ARRAY_TMP = copy(QUEST_ARRAY)
            for pod in pods:
                for T in QUEST_ARRAY_TMP:
                    if T[1] == pod['name']:
                        _async_raise(T[0], SystemExit)
                        QUEST_ARRAY.remove(T)

            return jsonify({
                "msg"       : f"[Pod.Post] stop monitor threads done",
                "result"    : 0,
            })
        else:
            print(f'[Pod.Post] unexpected option: {option}')
            return jsonify({
                "msg"       : f"[Pod.Post] unexpected option: {option}",
                "result"    : -1,
            })

@app.route('/services')
def Services():
    config = Config()
    services = getServices(config)
    return jsonify({
                    "services"   : services,
                    })

@socketio.on('connect',namespace='/test_conn')
def connect():
    print("connected")
    socketio.emit('connect_response',{'res':True},namespace='/test_conn')

@socketio.on('message',namespace='/test_conn')
def viewPod(subscribeName):
    print(f"[viewPod] {subscribeName}")
    print(f"start_new_thread {subscribeName}")

    if subscribeName in sending_data_threads.keys():
        _async_raise(sending_data_threads[subscribeName].ident,SystemExit)
        del sending_data_threads[subscribeName]

    pod_name,predict_model = subscribeName.split('_')

    if predict_model == 'monitor':
        thread = socketio.start_background_task(target=sending_monitor_thread, subscribe_name = subscribeName, load_data=load_monitor_data)
        sending_data_threads[subscribeName] = thread
    else:
        # 创建读数据thread
        thread = socketio.start_background_task(target=predict_thread, pod_name = pod_name, predict_model=predict_model)
        sending_data_threads[subscribeName] = thread

@socketio.on('stopPreviousSubscribe',namespace='/test_conn')
def stopPreviousSubscribe(subscribeName):
    print(f"[stopPreviousSubscribe] {subscribeName}")
    if subscribeName in sending_data_threads.keys():
        print(f"end_previous_subscribe_thread {subscribeName}")
        _async_raise(sending_data_threads[subscribeName].ident,SystemExit)
        del sending_data_threads[subscribeName]

def sending_monitor_thread(subscribe_name, load_data):
    pod_name,predict_model = subscribe_name.split('_')
    while True:
        data = load_data(pod_name, predict_model)
        print(f'[monitor_thread] len_data = {len(data)}')
        print(f'[monitor_thread] data = {data}')
        if data is None:
            socketio.sleep(15)
            continue
        socketio.emit(subscribe_name,{'data':data},namespace='/test_conn')
        socketio.sleep(15)

# 预测线程函数
def predict_thread(pod_name, predict_model):
    for latest_data_shape,res_final_shape in OT(pod_name, predict_model):
        data = load_predict_data(pod_name, predict_model)
        print(f'[predict_thread] len_data = {len(data)}')
        print(f'[predict_thread] data = {data}')
        if data is None:
            continue
        socketio.emit(pod_name+'_'+predict_model,{'data':data},namespace='/test_conn')
        socketio.sleep(5)

@app.route('/test/record_global')
def record_global_data():
    config = Config()
    node_pods = getPods(config,True)
    pod_names,_ = getPodNamesForNamespace()
    with open('node_pods.json','w') as f:
        json.dump(node_pods,f)
    monitor_pods(pod_names)
    return jsonify(node_pods)

@socketio.on('deploy',namespace='/test_conn')
def deploy():
    global deploy_th
    deploy_th = socketio.start_background_task(target=deploy_thread)

@socketio.on('stopDeploy',namespace='/test_conn')
def stopDeployThread():
    if deploy_th is not None:
        _async_raise(deploy_th.ident,SystemExit)

def send_deploy_info(migrations):
    node_pod_mappings = getMappingsForNamespace()
    nodes = []
    for node,pods in node_pod_mappings.items():
        monitor_datas=[]
        for pod in pods:
            monitor_data = queryOnce(pod)
            if "mem" in monitor_data.keys() and len(monitor_data["mem"])>=1:
                monitor_data["mem"] = float(monitor_data["mem"][1])/(8*10**9)*100
            if "cpu" in monitor_data.keys() and len(monitor_data["cpu"])>=1:
                monitor_data["cpu"] = float(monitor_data["cpu"][1])/4*100
            monitor_datas.append(monitor_data)
        nodes.append({"name":node,"pods":pods,"monitor_data":monitor_datas})
    socketio.emit('deploy_response',{'data':nodes,"migrations":migrations},namespace='/test_conn')

def deploy_thread():
    migrations={}
    while True:
        send_deploy_info(migrations)
        pod_names, _ = getPodNamesForNamespace()
        monitor_threads = monitor_pods(pod_names, True) # clear database
        socketio.sleep(300)
        
        migrations = oneMigration()
        for T in monitor_threads:
            _async_raise(T[0], SystemExit)

def oneMigration():
    # 1. initialize state
    pod_names, pod_deployment_mappings = getPodNamesForNamespace()
    pod_names_copy = copy(pod_names)
    for pod_name in pod_names_copy:
        if 'influxdb' in pod_name or 'webapp' in pod_name:
            pod_names.remove(pod_name)
    node_names = getNodeNamesForNamespace()
    node_pod_mappings = getMappingsForNamespace()
    deployment_names = podnames_to_deploymentnames(pod_names,pod_deployment_mappings)
    node_deployment_mappings = nodepodmappings_to_nodedeploymentmappings(node_pod_mappings,pod_deployment_mappings)

    state = State(deployment_names,node_names,node_deployment_mappings)
    
    # 2. initialize model
    actor_model = load_model('../../100server-95')

    # 3. create one time data
    raw_data = load_dataset_for_namespaced_pods(pod_names)
    deployment_raw_data = poddata_to_deploymentdata(raw_data, pod_deployment_mappings)
    state_data = state.create_state(deployment_raw_data)

    # 4. get action
    action = actor_model.get_action(state_data)
    
    # 5. decode action
    migrations = state.decode_action(action[0])

    # 6. execute migration
    handleMigrationAction(migrations)
    socketio.sleep(20)
    pod_names, pod_deployment_mappings = getPodNamesForNamespace()
    node_pod_mappings = getMappingsForNamespace()
    node_deployment_mappings = nodepodmappings_to_nodedeploymentmappings(node_pod_mappings,pod_deployment_mappings)
    for deployment_name,node_name in migrations.items():
        if deployment_name not in node_deployment_mappings[node_name]:
            print(f"Error: migrations not successful, migrations={migrations}, new node-deployment mappings={node_deployment_mappings}")

    return migrations


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
