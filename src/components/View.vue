<template>
    <div id="app"> 
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