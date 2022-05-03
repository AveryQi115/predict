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
                    <h1>View Dynamic Scheduling</h1>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-12">
                <div class="page-header">
                    <h1 id="typography">Migrations: {{migrations}}</h1>
                </div>
            </div>
        </div>
        <div class="row">
            <div class="col-lg-4">
                <div class = "bs-component ml-5" v-for="node, index in nodes" :key="index">
                    <div v-if="index%3==0" class="card border-primary mb-3" style="max-width: 20rem;">
                        <div class="card-header">{{node.name}}</div>
                        <div class="card-body">
                            <!-- <div class="progress">
                                <div v-if="node.max<=50" class="progress-bar progress-bar-striped bg-success" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=80 && node.max>50" class="progress-bar progress-bar-striped bg-warning" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=100 && node.max>80" class="progress-bar progress-bar-striped bg-danger" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <div class="card-header">
                                allocatable
                            </div>
                            <p class="card-text">
                                cpu: {{node.allocatable.cpu}}
                                mem: {{node.allocatable.memory}}
                                pods: {{node.allocatable.pods}}
                            </p>
                            <div class="card-header">
                                capacity
                            </div>
                            <p class="card-text">
                                cpu: {{node.capacity.cpu}}
                                mem: {{node.capacity.memory}}
                                pods: {{node.capacity.pods}}
                            </p> -->
                            <div class="accordion" id="accordionExample">
                                <div v-for="pod, podindex in node.pods" :key="podindex" class="accordion-item">
                                    <h2 class="accordion-header" :id="'heading'+podindex">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse'+podindex" aria-expanded="false" :aria-controls="'collapse'+podindex">
                                            {{pod}}
                                        </button>
                                    </h2>
                                    <div :id="'collapse'+podindex" class="accordion-collapse collapse show" :aria-labelledby="'heading'+podindex" data-bs-parent="#accordionExample" style="">
                                        <div class="accordion-body">
                                            {{node.monitor_data[podindex]}}
                                        </div>
                                    </div>
                                </div>
                            </div><!-- end of accordion -->
                        </div>
                    </div><!-- end of card -->
                </div><!-- end of bs-component -->
            </div><!-- end of col-lg-4 -->
            <div class="col-lg-4">
                <div class = "bs-component ml-5" v-for="node, index in nodes" :key="index">
                    <div v-if="index%3==1" class="card border-primary mb-3" style="max-width: 20rem;">
                        <div class="card-header">{{node.name}}</div>
                        <div class="card-body">
                            <!-- <div class="progress">
                                <div v-if="node.max<=50" class="progress-bar progress-bar-striped bg-success" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=80 && node.max>50" class="progress-bar progress-bar-striped bg-warning" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=100 && node.max>80" class="progress-bar progress-bar-striped bg-danger" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <div class="card-header">
                                allocatable
                            </div>
                            <p class="card-text">
                                cpu: {{node.allocatable.cpu}}
                                mem: {{node.allocatable.memory}}
                                pods: {{node.allocatable.pods}}
                            </p>
                            <div class="card-header">
                                capacity
                            </div>
                            <p class="card-text">
                                cpu: {{node.capacity.cpu}}
                                mem: {{node.capacity.memory}}
                                pods: {{node.capacity.pods}}
                            </p> -->
                            <div class="accordion" id="accordionExample">
                                <div v-for="pod, podindex in node.pods" :key="podindex" class="accordion-item">
                                    <h2 class="accordion-header" :id="'heading'+podindex">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse'+podindex" aria-expanded="false" :aria-controls="'collapse'+podindex">
                                            {{pod}}
                                        </button>
                                    </h2>
                                    <div :id="'collapse'+podindex" class="accordion-collapse collapse show" :aria-labelledby="'heading'+podindex" data-bs-parent="#accordionExample" style="">
                                        <div class="accordion-body">
                                            {{node.monitor_data[podindex]}}
                                        </div>
                                    </div>
                                </div>
                            </div><!-- end of accordion -->
                        </div>
                    </div><!-- end of card -->
                </div><!-- end of bs-component -->
            </div><!-- end of col-lg-4 -->
            <div class="col-lg-4">
                <div class = "bs-component ml-5" v-for="node, index in nodes" :key="index">
                    <div v-if="index%3==2" class="card border-primary mb-3" style="max-width: 20rem;">
                        <div class="card-header">{{node.name}}</div>
                        <div class="card-body">
                            <!-- <div class="progress">
                                <div v-if="node.max<=50" class="progress-bar progress-bar-striped bg-success" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=80 && node.max>50" class="progress-bar progress-bar-striped bg-warning" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                                <div v-if="node.max<=100 && node.max>80" class="progress-bar progress-bar-striped bg-danger" role="progressbar" :style="'width:'+node.max+'%;'" :aria-valuenow="node.max" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                            <div class="card-header">
                                allocatable
                            </div>
                            <p class="card-text">
                                cpu: {{node.allocatable.cpu}}
                                mem: {{node.allocatable.memory}}
                                pods: {{node.allocatable.pods}}
                            </p>
                            <div class="card-header">
                                capacity
                            </div>
                            <p class="card-text">
                                cpu: {{node.capacity.cpu}}
                                mem: {{node.capacity.memory}}
                                pods: {{node.capacity.pods}}
                            </p> -->
                            <div class="accordion" id="accordionExample">
                                <div v-for="pod, podindex in node.pods" :key="podindex" class="accordion-item">
                                    <h2 class="accordion-header" :id="'heading'+podindex">
                                        <button class="accordion-button" type="button" data-bs-toggle="collapse" :data-bs-target="'#collapse'+podindex" aria-expanded="false" :aria-controls="'collapse'+podindex">
                                            {{pod}}
                                        </button>
                                    </h2>
                                    <div :id="'collapse'+podindex" class="accordion-collapse collapse show" :aria-labelledby="'heading'+podindex" data-bs-parent="#accordionExample" style="">
                                        <div class="accordion-body">
                                            {{node.monitor_data[podindex]}}
                                        </div>
                                    </div>
                                </div>
                            </div><!-- end of accordion -->
                        </div>
                    </div><!-- end of card -->
                </div><!-- end of bs-component -->
            </div><!-- end of col-lg-4 -->
        </div><!-- end of row -->
    </div>
</template>

<script>
export default{
    name: "deploy",
    data(){
        return {
            nodes:[],
            migrations:{},
        };
    },
    created() {
      this.$socket.open();
      this.subsribe_name = 'deploy_response';
      this.$socket.emit('deploy');
      this.sockets.subscribe(this.subsribe_name, this.updateData);
    },
    destroyed() {
      this.$socket.close()
    },
    beforeDestroy() {
      this.$socket.emit('stopDeploy')
      this.sockets.unsubscribe(this.subsribe_name)
    },
    methods:{
        updateData: function(data){
            this.nodes = data['data'];
            this.migrations = data['migrations'];
        }
    },
    sockets: {},
    mounted () {
      this.sockets.subscribe(this.subsribe_name, this.updateData)
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