import torch as th
import torch.nn as nn
import torch.autograd as autograd
import pandas as pd
import time
import numpy as np

NODE_NUM = 2
POD_NUM = 6

'''
    action model
'''
class QmixAgentForDeploy(nn.Module):
    def __init__(self, state_space, act_space, args):
        super(QmixAgentForDeploy, self).__init__()
        self.state_space = state_space
        self.act_space = act_space

        self.features = nn.Sequential(
            nn.Conv2d(self.state_space[0],32,kernel_size=2,stride=1),
            nn.ReLU(),
            nn.Conv2d(32,64,kernel_size=2,stride=1),
            nn.ReLU(),
            nn.Conv2d(64,64,kernel_size=2,stride=1),
            nn.ReLU()
        )

        self.fc = nn.Sequential(
            nn.Linear(self.feature_size(),512),
            nn.ReLU(),
            nn.Linear(512,self.act_space)
        )

    def feature_size(self):
        print(self.state_space)
        return self.features(autograd.Variable(th.zeros(1,*self.state_space))).view(1,-1).size(-1)
    
    def forward(self, x):
        # import pdb
        # pdb.set_trace()
        x = th.tensor(x,dtype=th.float32)
        if x.dim()==4:
            x = th.transpose(x,1,3)
            x = x.reshape(-1,x.shape[1],x.shape[2],x.shape[3])
        else:
            x = th.transpose(x,0,2)
            x = x.reshape(-1,x.shape[0],x.shape[1],x.shape[2])
        x = self.features(x)
        x = x.view(x.size(0),-1)
        x = self.fc(x)
        return x

    def get_action(self, data):
        x = self.forward(data)
        x_min,_ = th.min(x,1)
        x_min = x_min.unsqueeze(1)
        x_max,_ = th.max(x,1)
        x_max = x_max.unsqueeze(1)
        x = th.sub(x,x_min)/(x_max-x_min)*(NODE_NUM-1)
        actions = th.round(x).cpu().detach().numpy().astype(int)# 9 and 0 has relatively low possibility to get
        return actions

class State():
    def __init__(self, pod_names, node_names, mappings):
        assert len(pod_names)==POD_NUM and len(node_names)==NODE_NUM, f'invalid pod length or node length for service-predict: len(pod_names)={len(pod_names)}, len(node_names)={len(node_names)}'
        self.create_dict(pod_names, node_names)
        self.create_mappings(mappings)

    def create_mappings(self, mappings):
        self.mappings = {}
        for node,pods in mappings.items():
            for pod in pods:
                self.mappings[pod] = node

    def create_dict(self,pod_names,node_names):
        pod_dict={}
        pod_counter = 0
        node_dict={}
        node_counter = 0
        self.pods = []
        self.nodes = []
        for pod in pod_names:
            pod_dict[pod] = pod_counter
            pod_counter += 1
            self.pods.append(pod)
        for node in node_names:
            node_dict[node] = node_counter
            node_counter += 1
            self.nodes.append(node)
        self.pod_dict = pod_dict
        self.node_dict = node_dict

    # raw_data is a dict, key is pod name, value is the datasets
    # datasets is a list of [time,cpu_usage,mem_usage] data
    def create_state(self, raw_data):
        df = self.create_df(raw_data)
        df = self.sample_df(df)
        state_data = self.format_data(df)
        return state_data

    def create_df(self, raw_data):
        df = pd.DataFrame(columns=['start_time','node_id','pod_id','used_cpu','used_mem'])
        for pod, pod_data in raw_data.items():
            pod_id = self.pod_dict[pod]
            node_id = self.node_dict[self.mappings[pod]]
            for data in pod_data:
                time_array = time.strptime(data[0],'%Y-%m-%dT%H:%M:%S.%fZ')
                start_time = int(time.mktime(time_array))
                cpu_usage = data[1]
                mem_usage = data[2]
                df.loc[len(df)] = [start_time,node_id,pod_id,cpu_usage,mem_usage]
        df = df.sort_values('start_time')
        latest_time = df.loc[len(df)-1,'start_time']
        latest_df = df[(df['start_time']<=latest_time) & (df['start_time']>= (latest_time-300))]
        time_begin = int(latest_df['start_time'].min())
        latest_df = latest_df.assign(start_time=lambda x:x.start_time-time_begin)
        df['start_time'] = df['start_time'].astype(int)
        df['node_id'] = df['node_id'].astype(int)
        df['pod_id'] = df['pod_id'].astype(int)
        return latest_df

    def sample_df(self, df):
        step = int(df['start_time'].min())
        request = pd.DataFrame(columns=['start_time','node_id','pod_id','used_cpu','used_mem'])
        for t in range(step, step+300, 30):
            selected_df = df[(df['start_time']>=t) & (df['start_time']<(t+30))]
            selected_df = selected_df.assign(start_time=t)
            added = selected_df.groupby('pod_id').mean().reset_index()
            request = request.append(added)
            for i in range(POD_NUM):
                if i not in added['pod_id'].values:
                    request_i = df[(df['start_time']<t) & (df['pod_id']==i)]
                    request_add = request_i.sort_values('start_time').iloc[len(request_i)-1]
                    request_add['start_time'] = t
                    request.loc[len(request)] = request_add
        
        request['start_time'] = request['start_time'].astype(int)
        request['node_id'] = request['node_id'].astype(int)
        request['pod_id'] = request['pod_id'].astype(int)
        assert len(request) == POD_NUM*10, f'{request}'
        return request

    def format_data(self,df):
        ret=[]
        step = int(df['start_time'].min())
        for t in range(step,step+300,30):
            for node in range(NODE_NUM):
                node_data = []
                node_df = df[df['node_id']==node]
                node_df = node_df.sort_values('pod_id')
                for pod_id in node_df['pod_id'].unique():
                    pod_data = node_df[(node_df['start_time']==t) & (node_df['pod_id']==pod_id)]
                    assert len(pod_data)==1, f'{pod_data},{node_df},{t}'
                    node_data.append([float(pod_data['used_cpu'].values),float(pod_data['used_mem'].values)])
                for i in range(POD_NUM-len(node_df['pod_id'].unique())):
                    node_data.append([0.0,0.0])
                ret.append(node_data)
        ret_np = np.array(ret)
        assert ret_np.shape==(10*NODE_NUM,POD_NUM,2),f'{ret_np.shape}'
        return ret_np

    def decode_action(self,action):
        migrations = {}
        for pod_index,node_index in enumerate(action):
            pod_name = self.pods[pod_index]
            node_name = self.nodes[node_index]
            migrations[pod_name] = node_name
        return migrations

def load_model(path):
    state_space = (2,10*NODE_NUM,POD_NUM)  # (resource_num,node_num*10,pod_num)
    action_space = POD_NUM                # pod_num
    actor_model = QmixAgentForDeploy(state_space,action_space,None)
    actor_model.load_state_dict(th.load("{}/agent.th".format(path), map_location=lambda storage, loc: storage))
    return actor_model
