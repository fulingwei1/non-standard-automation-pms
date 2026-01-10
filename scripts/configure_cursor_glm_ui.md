# Cursor GLM-4.7 自动配置指南

由于 Cursor 的自定义模型配置需要通过 UI 界面完成，我为您创建了详细的配置步骤和自动化辅助工具。

## 快速配置（推荐方式）

### 方式一：使用配置助手脚本

我已经创建了一个配置脚本，它会：
1. 备份您的当前设置
2. 在配置文件中添加 GLM 相关配置（如果支持）
3. 提供详细的 UI 配置步骤

运行脚本：
```bash
cd /Users/flw/non-standard-automation-pm
python3 scripts/configure_cursor_glm.py
```

### 方式二：手动 UI 配置（最可靠）

由于 Cursor 的架构，最可靠的方式是通过 UI 配置：

#### 步骤 1: 打开 Cursor 设置
- 按 `Cmd + ,` 打开设置
- 或点击左下角 ⚙️ → Settings

#### 步骤 2: 进入 Models 配置
- 在设置搜索框输入：`Models`
- 或导航到：**Cursor** → **Models**

#### 步骤 3: 添加自定义模型
- 点击 **"Add Custom Model"** 或 **"+"** 按钮
- 选择协议：**OpenAI**

#### 步骤 4: 填写配置信息

**复制以下信息到对应字段：**

```
Provider Name: GLM-4.7
（或任意您喜欢的名称）

OpenAI API Key:
6f80249e3d434099a3fb8c898f9b65ef.OmqhpVVwiQaNLkDp

Override OpenAI Base URL:
https://open.bigmodel.cn/api/coding/paas/v4

Model Name:
GLM-4.7
```

⚠️ **重要**：
- Model Name 必须使用**大写**：`GLM-4.7`
- 不要使用小写：`glm-4.7` ❌
- 确保 API Key 没有多余的空格

#### 步骤 5: 保存并测试
- 点击 **Save** 或 **✓** 保存
- 在 Cursor 主界面或聊天窗口的模型选择器中选择 **GLM-4.7**
- 发送测试消息验证配置

## 配置信息速查

```
API Key: 6f80249e3d434099a3fb8c898f9b65ef.OmqhpVVwiQaNLkDp
Base URL: https://open.bigmodel.cn/api/coding/paas/v4
Model Name: GLM-4.7
```

## 验证配置

配置完成后，测试步骤：

1. 打开 Cursor 聊天界面（`Cmd + L`）
2. 查看右上角或底部的模型选择器
3. 应该能看到 **GLM-4.7** 选项
4. 选择 GLM-4.7 后发送测试消息：
   ```
   你好，请用中文回复
   ```
5. 如果收到中文回复，说明配置成功 ✅

## 常见问题

### ❌ 找不到 "Add Custom Model" 按钮
**原因**: 您可能不是 Cursor 高级会员  
**解决**: 需要 Cursor Pro 或更高版本

### ❌ 提示 "The model GLM does not work with your current plan"
**原因**: 会员等级不足  
**解决**: 升级到 Cursor Pro 或 Business 版本

### ❌ 模型无法响应
**检查**:
- API Key 是否正确（无多余空格）
- Base URL 是否正确
- Model Name 是否大写
- 智谱平台 API Key 是否有效

## 需要帮助？

- 详细文档：`docs/CURSOR_GLM_QUICK_SETUP.md`
- 完整配置指南：`docs/CURSOR_GLM_CONFIG.md`
