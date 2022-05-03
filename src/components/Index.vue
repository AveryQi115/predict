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
            </div>
        </div>    
        <div class="row">
            <div class="col-lg-12">
                <img src="../assets/index.jpeg" style="width:75%;height:75%;"/>
            </div>
        </div> 
    </div>
</template>

<script>
export default{
    data(){
        return {
        };
    },
}

</script>

<style>
@import "../../public/bootstrap.min.css";
.page-header {
    margin-top: 30px;
    margin-bottom: 30px;
}
</style>