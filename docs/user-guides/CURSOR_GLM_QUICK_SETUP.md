# Cursor GLM-4.7 快速配置指南

## 您的配置信息

**API Key**: `6f80249e3d434099a3fb8c898f9b65ef.OmqhpVVwiQaNLkDp`  
**Base URL**: `https://open.bigmodel.cn/api/coding/paas/v4`  
**Model Name**: `GLM-4.7`

## 配置步骤（5分钟完成）

### 方法一：通过 Cursor UI 配置（推荐）

1. **打开 Cursor 设置**
   - 按 `Cmd + ,` (macOS) 或 `Ctrl + ,` (Windows/Linux)
   - 或点击左下角 ⚙️ 图标 → Settings

2. **进入 Models 配置**
   - 在设置搜索框输入：`Models`
   - 或导航到：**Cursor** → **Models**

3. **添加自定义模型**
   - 点击 **"Add Custom Model"** 或 **"+"** 按钮
   - 选择协议：**OpenAI**

4. **填写配置信息**
   
   复制以下信息到对应字段：

   ```
   Provider Name: GLM-4.7 (或任意名称)
   
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

5. **保存并切换**
   - 点击 **Save** 或 **✓** 保存
   - 在 Cursor 主界面或聊天窗口的模型选择器中选择 **GLM-4.7**

### 方法二：验证配置是否成功

配置完成后，测试步骤：

1. 打开 Cursor 聊天界面（`Cmd + L` 或 `Ctrl + L`）
2. 查看右上角或底部的模型选择器
3. 应该能看到 **GLM-4.7** 选项
4. 选择 GLM-4.7 后发送一条测试消息：
   ```
   你好，请用中文回复
   ```
5. 如果收到中文回复，说明配置成功 ✅

## 常见问题排查

### ❌ 问题1: 找不到 "Add Custom Model" 按钮

**原因**: 您可能不是 Cursor 高级会员

**解决方案**:
- 检查 Cursor 订阅状态
- 需要 **Cursor Pro** 或更高版本
- 升级链接：https://cursor.sh/pricing

### ❌ 问题2: 提示 "The model GLM does not work with your current plan"

**原因**: 会员等级不足

**解决方案**: 升级到 Cursor Pro 或 Business 版本

### ❌ 问题3: 模型无法响应或报错

**检查清单**:
- [ ] API Key 是否正确复制（没有多余空格）
- [ ] Base URL 是否正确：`https://open.bigmodel.cn/api/coding/paas/v4`
- [ ] Model Name 是否大写：`GLM-4.7`
- [ ] 智谱平台 API Key 是否有效（检查余额和权限）

### ❌ 问题4: 找不到 Models 设置

**解决方案**:
1. 确保 Cursor 版本是最新的
2. 尝试重启 Cursor
3. 检查是否在正确的设置页面（Cursor Settings，不是 VS Code Settings）

## 配置验证清单

配置完成后，请确认：

- [ ] ✅ 在模型选择器中能看到 GLM-4.7
- [ ] ✅ 可以成功切换到 GLM-4.7
- [ ] ✅ 发送消息后能收到回复
- [ ] ✅ 回复内容正常（不是错误信息）

## 其他可用模型

如果 GLM-4.7 不可用，可以尝试：

- `GLM-4.6` - 上一版本
- `GLM-4.5-air` - 轻量版本

配置方法相同，只需修改 Model Name。

## 需要帮助？

如果遇到问题：

1. 检查 [智谱开放平台](https://open.bigmodel.cn/) 的 API Key 状态
2. 查看 [Cursor 官方文档](https://cursor.sh/docs)
3. 参考详细配置文档：`docs/CURSOR_GLM_CONFIG.md`

---

**配置日期**: 2025-01-21  
**状态**: 待配置  
**下一步**: 按照上述步骤在 Cursor UI 中完成配置
