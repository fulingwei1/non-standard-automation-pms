<template>
  <div class="placeholder-page">
    <el-empty description="功能开发中...">
      <el-button type="primary" @click="$router.back()">返回</el-button>
    </el-empty>
  </div>
</template>

<style scoped>
.placeholder-page {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
