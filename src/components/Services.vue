<template>
    <div id="app"> 
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
            <div class="container-fluid">
                <a class="navbar-brand" href="#">Dynamic Deployment</a>
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
                    <b-link class="nav-link" :to="{ path: '/Pods'}" replace>Predict</b-link>
                    </li>
                    <li class="nav-item">
                    <b-link class="nav-link" :to="{ path: '/Nodes'}" replace>Scheduling</b-link>
                    </li>
                    <li class="nav-item">
                        <b-dropdown id="dropdown-1" text="Monitor" variant="dark">
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Pods'}" replace>Pods</b-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Services'}" replace>Services</b-link>
                            </b-dropdown-item>
                            <b-dropdown-item>
                                <b-link class="dropdown-item" :to="{ path: '/Deployments'}" replace>Deployments</b-link>
                            </b-dropdown-item>
                        </b-dropdown>
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
                            <th scope="col">Service</th>
                            <th scope="col">Spec</th>
                        </tr>
                        </thead>
                        <tbody>
                        <tr v-for="service, index in services" :key="index">
                            <th scope="row">{{service.name}}</th>
                            <td>
                                <vue-blob-json-csv
                                    @success="handleSuccess"
                                    @error="handleError"
                                    tag-name="div"
                                    file-type="json"
                                    file-name="spec"
                                    :data="service.spec"
                                    confirm="Do you want to download it?"
                                >
                                <button class="btn btn-dark">Download Spec</button>
                                </vue-blob-json-csv>
                            </td>
                        </tr>
                        
                        </tbody>
                    </table>
                </div><!-- /example -->
            </div>
        </div>    
    </div>
</template>

<script>
import axios from 'axios';
export default{
    data(){
        return {
            services:[],
        };
    },
    methods:{
        getResponse(){
            const path="http://localhost:5000/services";
            axios.get(path)
            .then((res) =>{
                console.log(res.data)
                this.services=res.data.services;
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