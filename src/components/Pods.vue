<template>
    <div id="app"> 
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">Monitor</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarColor01" aria-controls="navbarColor01" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
                </button>

                <div class="collapse navbar-collapse" id="navbarColor01">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                    <b-link class="nav-link active" :to="{ path: '/'}" replace>Home
                        <span class="visually-hidden">(current)</span>
                    </b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Pods'}" replace>Pods</b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Services'}" replace>Services</b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Deployments'}" replace>Deployments</b-link>
                    </li>
                </ul>
                </div>
            </div>
        </nav>
        <div class="row">
            <div class="col-lg-12">
                <div class="page-header">
                    <h1>View Your Application</h1>
                </div>

                <div class="bs-component">
                    <table class="table table-hover">
                        <thead>
                        <tr>
                            <th scope="col">Pod</th>
                            <th scope="col">Label</th>
                            <th scope="col">Spec</th>
                            <th scope="col">Status</th>
                            <th scope="col">Select</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr v-for="pod, index in pods" :key="index" :class="pod.monitored">
                            <th scope="row">{{pod.name}}</th>
                            <td>{{pod.label}}</td>
                            <td>
                                <vue-blob-json-csv
                                    @success="handleSuccess"
                                    @error="handleError"
                                    tag-name="div"
                                    file-type="json"
                                    file-name="spec"
                                    :data="pod.spec"
                                    confirm="Do you want to download it?"
                                >
                                <button class="btn btn-dark">Download Spec</button>
                                </vue-blob-json-csv>
                            </td>
                            <td v-if="pod.monitored">
                                <b-link class="nav-link" :to="{ path: `/View/${pod.name}`}" replace>Monitoring</b-link>
                            </td>
                            <td v-else>
                                Default
                            </td>
                            <td>
                                <input class="form-check-input" type="checkbox" v-model="selectedPods" :value="pod"/>
                                <!-- <v-btn class="btn btn-outline-success" @click="addmonitor(pod)"><v-icon>add</v-icon></v-btn> -->
                            </td>
                        </tr>
                        
                        </tbody>
                    </table>
                </div><!-- /example -->
            </div>
        </div> 
        <div class="row">
            <div class="col-lg-4">
                <div class="bs-component">
                    <ul class="list-group">
                        <li class="list-group-item d-flex justify-content-between align-items-center" v-for="selectPod, index in selectedPods" :key="index">
                        {{selectPod.name}}
                            <span class="badge bg-primary rounded-pill">1</span>
                        </li>
                    </ul>
                </div>
            </div>
            <div class="col-lg-4">
                <b-form-timepicker v-model="time" show-seconds locale="en"></b-form-timepicker>
            </div>    
            <div class="col-lg-4">
                <fieldset class="form-group">
                    <legend>Options</legend>
                    <div class="form-check">
                      <label class="form-check-label">
                        <input type="radio" v-model="option" class="form-check-input" name="monitor" id="" value="monitor" checked="">
                        Add Monitor Threads
                      </label>
                    </div>
                    <div class="form-check">
                      <label class="form-check-label">
                        <input type="radio" v-model="option" class="form-check-input" name="stop" id="" value="stop">
                        Stop Monitor Threads
                      </label>
                    </div>
                  </fieldset>
            </div>
        </div>
        <div class="row">
            <button class="btn btn-lg btn-primary" type="button" @click="postoperation">confirm</button>
        </div>    
    </div>
</template>

<script>
import axios from 'axios';
export default{
    data(){
        return {
            pods:[],
            selectedPods:[],
            option: '',
            time:'',
        };
    },
    methods:{
        getResponse(){
            const path="http://localhost:5000/pods";
            axios.get(path)
            .then((res) =>{
                console.log(res.data)
                this.pods=res.data.pods;
            })
            .catch((err) =>{
                console.error(err);
            });
        },

        postoperation:function(){
            const path="http://localhost:5000/pods";
            console.log(this.selectedPods);
            console.log(this.time);
            console.log(this.option);
            axios.post(path,{
                "SelectedPods":this.selectedPods,
                "StartTime":this.time,
                "option":this.option,
            })
            .then((res) =>{
                console.log(res.data);
            })
            .catch((err) =>{
                console.error(err);
            });
        },
    },
    created(){
        this.getResponse();
    }
}

</script>

<style>
@import "../../public/bootstrap.min.css";
.page-header {
    margin-top: 30px;
    margin-bottom: 30px;
}
</style>