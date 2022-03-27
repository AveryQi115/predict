from kubernetes import client, config
import ast
from kubernetes.client import V1NodeSelectorRequirement, V1NodeSelector, V1Affinity, V1NodeAffinity, V1NodeSelectorTerm

class Config():
    def __init__(self):
        config.load_kube_config("./config")
        self.core_api = client.CoreV1Api()
        self.deployment_api = client.AppsV1Api()
    
def getDeployments(config):
    deployments = config.deployment_api.list_namespaced_deployment(namespace='service-predict').items
    items = []
    for deployment in deployments:
        item = {}
        item["name"] = deployment.metadata.name
        item["replicas"] = deployment.spec.replicas
        item["template"] = ast.literal_eval(str(deployment.spec.template))
        item["availble_replicas"] = deployment.status.available_replicas
        items.append(item)
    return items

def getServices(config):
    services = config.core_api.list_namespaced_service(namespace="service-predict").items
    items = []
    for service in services:
        item = {}
        item["name"] = service.metadata.name
        item["spec"] = ast.literal_eval(str(service.spec))
        items.append(item)
    return items

def getPods(config, nodeGatherer=False):
    pods = config.core_api.list_namespaced_pod(namespace='service-predict').items
    if nodeGatherer==False:
        items = []
        for pod in pods:
            item = {}
            item["name"] = pod.metadata.name
            item["label"] = pod.metadata.labels
            item["spec"] = ast.literal_eval(str(pod.spec))
            items.append(item)
        return items
    else:
        items = {}
        for pod in pods:
            node = pod.spec.node_name
            item = {}
            item["name"] = pod.metadata.name
            item["label"] = pod.metadata.labels
            item["spec"] = ast.literal_eval(str(pod.spec))
            if node in items.keys():
                items[node].append(item)
            else:
                items[node] = [item]
        return items

def getNodes(config):
    nodes = config.core_api.list_node().items
    pods = getPods(config,nodeGatherer=True)
    items = []
    for node in nodes:
        item = {}
        item['labels'] = node.metadata.labels
        item['name'] = node.metadata.name
        item['namespace'] = node.metadata.namespace
        if node.spec.taints is None:
            item['taints'] = None
        else:
            item['taints'] = [{'key':x.key,'value':x.value,'effect':x.effect} for x in node.spec.taints]
        item['addresses'] = [{'address': x.address,'type':x.type} for x in node.status.addresses]
        item['allocatable'] = node.status.allocatable
        item['capacity'] = node.status.capacity
        if item['name'] in pods.keys():
            item['pods'] = pods[item['name']]
        else:
            item['pods'] = None
        items.append(item)
    return items

def getPodNamesForNamespace():
    config = Config()
    node_pods = getPods(config,True)
    pod_names = []
    deployment_mappings = {}
    for _,pods in node_pods.items():
        for pod in pods:
            pod_names.append(pod["name"])
            deployment_name = "-".join(pod["name"].split("-")[:-2]) # TODO: not real deployment name, warning
            deployment_mappings[pod["name"]]=deployment_name
    return pod_names, deployment_mappings

def getNodeNamesForNamespace():
    config = Config()
    node_pods = getPods(config,True)
    node_names = list(node_pods.keys())
    return node_names

def getMappingsForNamespace():
    config = Config()
    node_pods = getPods(config,True)
    node_pods_dict = {}
    for node, pods in node_pods.items():
        node_pods_dict[node] = []
        for pod in pods:
            node_pods_dict[node].append(pod["name"])
    return node_pods_dict



def checkPodExist(pod_name):
    config = Config()
    client_v1 = config.deployment_api
    try:
        res = client_v1.read_namespaced_deployment(pod_name, "service-predict")
        if res.spec.replicas!=1:
            return (False, None)
    except:
        return (False, None)
    return (True, res)

def checkNodeExist(node_name):
    config = Config()
    client_v1 = config.core_api
    try:
        client_v1.read_node(node_name)
    except:
        return False
    return True

def CreateNewPod(pod_name, node_name, deployment):
    config = Config()
    client_v1 = config.deployment_api
    requirements = [V1NodeSelectorRequirement(key="kubernetes.io/hostname", operator="In", values=[node_name])]
    deployment.spec.template.spec.affinity = V1Affinity(node_affinity=V1NodeAffinity(required_during_scheduling_ignored_during_execution=V1NodeSelector(node_selector_terms = [V1NodeSelectorTerm(match_expressions=requirements)])))
    try:
        client_v1.replace_namespaced_deployment(pod_name, "service-predict", deployment)
    except:
        print(f'Add Node Selector Rule failed.')
        return

# actions is a dict of PodName: NodeName
# the PodName has to be a Deployment Name also
def handleMigrationAction(actions):
    for key,value in actions.items():
        pod_name = key
        node_name = value
        exist, pod = checkPodExist(pod_name)
        if not exist:
            print(f"Pod {pod_name} not exists.")
            continue

        if not checkNodeExist(node_name):
            print(f"Node {node_name} not exists.")
            continue

        CreateNewPod(pod_name, node_name, pod)