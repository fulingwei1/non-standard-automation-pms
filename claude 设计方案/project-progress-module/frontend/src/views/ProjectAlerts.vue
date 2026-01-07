<template>
  <div class="project-alerts-page">
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2>项目预警</h2>
    </div>
    <el-card>
      <el-empty description="项目预警页面，请前往预警中心查看全部预警">
        <el-button type="primary" @click="$router.push('/alerts')">前往预警中心</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
defineProps({ projectId: { type: Number, required: true } })
</script>

<style scoped>
.project-alerts-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
</style>
