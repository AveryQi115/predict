<template>
    <div id="app"> 
    </div>
</template>

<script>
  export default {
    name : 'test',
    data() {
      return {
        graphData:[],
      }
    },
    created() {
      this.$socket.open()
      this.$socket.emit('message', this.$route.params.pod_name)
      this.sockets.subscribe('result', data => {
        console.log('result ', data)
      }) 
    },
    destroyed() {
      this.$socket.close()
    },
    beforeDestroy() {
      this.sockets.unsubscribe('result')
    },
    methods: {
    },
    sockets: {
      result: data => {
          console.log('result', data)
      }
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