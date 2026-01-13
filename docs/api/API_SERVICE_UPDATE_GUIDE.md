# API 服务更新指南

> **目的**: 手动添加自动化处理 API 到前端 API 服务中

---

## 一、更新位置

**文件路径**: `frontend/src/services/api.js`

**目标位置**: `progressApi.analytics` 对象中

---

## 二、具体更新步骤

### 步骤 1: 找到 progressApi.analytics

在文件中搜索 `progressApi.analytics`，你会看到类似这样的代码：

```javascript
analytics: {
  getForecast: (projectId) =>
    api.get(`/progress/projects/${projectId}/progress-forecast`),
  checkDependencies: (projectId) =>
    api.get(`/progress/projects/${projectId}/dependency-check`),
},
```

### 步骤 2: 在 analytics 对象中添加 autoProcess

在 `checkDependencies` 方法后面添加 `autoProcess` 对象：

```javascript
analytics: {
  getForecast: (projectId) =>
    api.get(`/progress/projects/${projectId}/progress-forecast`),
  checkDependencies: (projectId) =>
    api.get(`/progress/projects/${projectId}/dependency-check`),
  
  // 新增：自动化处理API
  autoProcess: {
    applyForecast: (projectId, params) =>
      api.post(`/progress/projects/${projectId}/auto-apply-forecast`, null, {
        params: {
          auto_block: params?.autoBlock,
          delay_threshold: params?.delayThreshold || 7
        }
      }),
    
    fixDependencies: (projectId, params) =>
      api.post(`/progress/projects/${projectId}/auto-fix-dependencies`, null, {
        params: {
          auto_fix_timing: params?.autoFixTiming,
          auto_fix_missing: params?.autoFixMissing !== false // 默认为true
        }
      }),
    
    runCompleteProcess: (projectId, options) =>
      api.post(`/progress/projects/${projectId}/auto-process-complete`, options),
    
    preview: (projectId, params) =>
      api.get(`/progress/projects/${projectId}/auto-preview`, {
        params: {
          auto_block: params?.autoBlock || false,
          delay_threshold: params?.delayThreshold || 7
        }
      }),
    
    batchProcess: (projectIds, options) =>
      api.post(`/progress/projects/batch/auto-process`, {
        project_ids: projectIds,
        options: options
      })
  }
},
```

### 步骤 3: 保存文件

保存 `frontend/src/services/api.js` 文件。

---

## 三、验证更新

### 3.1 检查文件

在浏览器控制台中运行：

```javascript
import { progressApi } from './services/api';

console.log(progressApi.analytics.autoProcess);
```

应该能看到 `autoProcess` 对象包含所有方法。

### 3.2 测试 API 调用

在前端页面中测试 API 调用：

```javascript
// 测试预览
const previewData = await progressApi.analytics.autoProcess.preview(1, {
  auto_block: false,
  delay_threshold: 7
});

// 测试执行
const result = await progressApi.analytics.autoProcess.runCompleteProcess(1, {
  auto_block: false,
  delay_threshold: 7,
  auto_fix_timing: false,
  auto_fix_missing: true,
  send_notifications: true
});
```

---

## 四、完整代码示例

### 更新前的代码

```javascript
export const progressApi = {
  // ... 其他代码 ...
  
  analytics: {
    getForecast: (projectId) =>
      api.get(`/progress/projects/${projectId}/progress-forecast`),
    checkDependencies: (projectId) =>
      api.get(`/progress/projects/${projectId}/dependency-check`),
  },
  
  // ... 其他代码 ...
};
```

### 更新后的代码

```javascript
export const progressApi = {
  // ... 其他代码 ...
  
  analytics: {
    getForecast: (projectId) =>
      api.get(`/progress/projects/${projectId}/progress-forecast`),
    checkDependencies: (projectId) =>
      api.get(`/progress/projects/${projectId}/dependency-check`),
    
    // 新增：自动化处理API
    autoProcess: {
      applyForecast: (projectId, params) =>
        api.post(`/progress/projects/${projectId}/auto-apply-forecast`, null, {
          params: {
            auto_block: params?.autoBlock,
            delay_threshold: params?.delayThreshold || 7
          }
        }),
      
      fixDependencies: (projectId, params) =>
        api.post(`/progress/projects/${projectId}/auto-fix-dependencies`, null, {
          params: {
            auto_fix_timing: params?.autoFixTiming,
            auto_fix_missing: params?.autoFixMissing !== false
          }
        }),
      
      runCompleteProcess: (projectId, options) =>
        api.post(`/progress/projects/${projectId}/auto-process-complete`, options),
      
      preview: (projectId, params) =>
        api.get(`/progress/projects/${projectId}/auto-preview`, {
          params: {
            auto_block: params?.autoBlock || false,
            delay_threshold: params?.delayThreshold || 7
          }
        }),
      
      batchProcess: (projectIds, options) =>
        api.post(`/progress/projects/batch/auto-process`, {
          project_ids: projectIds,
          options: options
        })
    }
  },
  
  // ... 其他代码 ...
};
```

---

## 五、常见问题

### Q1: 找不到 progressApi.analytics？

**A**: 在文件中搜索 `export const progressApi`，然后在该对象内部查找 `analytics` 属性。

### Q2: 更新后页面报错？

**A**: 检查以下几点：
1. 语法是否正确（括号、逗号）
2. 缩进是否正确
3. 是否有重复的方法名
4. 浏览器控制台是否有错误信息

### Q3: API 调用失败？

**A**: 检查以下几点：
1. 后端服务是否启动
2. 后端路由是否正确配置
3. 请求参数是否正确
4. 用户是否登录且有权限

---

## 六、完成验证

### 6.1 后端验证

```bash
# 检查后端服务是否启动
curl http://localhost:8000/health

# 检查新API是否可用
curl -X GET "http://localhost:8000/api/v1/progress/projects/1/auto-preview" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6.2 前端验证

```bash
# 启动前端服务
npm start

# 访问进度预测页面
# http://localhost:3000/projects/1/progress-forecast

# 访问依赖巡检页面
# http://localhost:3000/projects/1/dependency-check
```

### 6.3 功能验证

1. ✅ 页面正常加载
2. ✅ 点击"预览自动处理"按钮
3. ✅ 查看预览对话框
4. ✅ 点击"确认执行"按钮
5. ✅ 查看执行结果

---

## 七、总结

**需要手动更新的文件**: 1个

- ✅ `frontend/src/services/api.js` - 添加 autoProcess API 方法

**已自动更新的文件**: 4个

- ✅ `app/services/progress_auto_service.py` - 自动化处理服务
- ✅ `app/api/v1/endpoints/progress/auto_processing.py` - API端点
- ✅ `app/scheduler_progress.py` - 定时任务配置
- ✅ `frontend/src/pages/ProgressForecast.jsx` - 进度预测看板页面
- ✅ `frontend/src/pages/DependencyCheck.jsx` - 依赖巡检结果页面
- ✅ `frontend/src/routes/routeConfig.jsx` - 路由配置

**完成后**: 所有功能100%可用

---

**最后更新**: 2026-01-12
