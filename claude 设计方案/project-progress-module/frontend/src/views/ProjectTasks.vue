<template>
  <div class="project-tasks-page">
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
      <h2>项目任务列表</h2>
    </div>
    <el-card>
      <el-empty description="任务列表页面开发中，请使用WBS或甘特图查看任务">
        <el-button type="primary" @click="$router.push(`/project/${projectId}/gantt`)">打开甘特图</el-button>
        <el-button @click="$router.push(`/project/${projectId}/wbs`)">打开WBS</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup>
defineProps({ projectId: { type: Number, required: true } })
</script>

<style scoped>
.project-tasks-page { padding: 20px; background: #f0f2f5; min-height: 100%; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.page-header h2 { margin: 0; }
</style>
