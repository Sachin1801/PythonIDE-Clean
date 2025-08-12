<template>
  <div class="v-header">
    <!-- <div class="v-collapse-btn" @click="$emit('update:collapse', !collapse)"> -->
    <!-- <div class="v-collapse-btn" @click="$emit('reverseCollapse')"> -->
    <div class="v-collapse-btn" @click="$emit('reverseCollapse', !collapse)">
      <ChevronRight v-if="collapse" :size="24" style="color: #fff;" />
      <ChevronLeft v-else :size="24" style="color: #fff;" />
    </div>
    <div class="v-title">Element Component Display</div>
  </div>
</template>

<script>
import { ChevronRight, ChevronLeft } from 'lucide-vue-next';

export default {
  props: {
    collapse: Boolean,
  },
  data() {
    return {
    }
  },
  components: {
    ChevronRight,
    ChevronLeft
  }
}
</script>

<style scoped>
.v-header {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 70px;
  background: #242F41;
  color: #fff;
  font-size: 22px;
}
.v-header .v-collapse-btn {
  float: left;
  line-height: 70px;
  padding: 2px 21px;
}
.v-header .v-title {
  float: left;
  width: 180px;
  line-height: 70px;
}
</style>