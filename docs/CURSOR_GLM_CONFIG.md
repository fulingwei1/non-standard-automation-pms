# Cursor 配置 GLM-4.7 模型指南

## 前置条件

⚠️ **重要提示**：
- 只有 **Cursor 高级会员及以上** 才能使用自定义模型配置
- 如果不是高级会员，配置后会报错：`The model GLM does not work with your current plan or api key`

## 配置步骤

### 1. 获取智谱 AI API Key

1. 访问 [智谱开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 进入控制台，创建 API Key
4. 复制保存您的 API Key（格式类似：`xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

### 2. 在 Cursor 中配置模型

#### 方法一：通过 UI 界面配置（推荐）

1. **打开 Cursor 设置**
   - 点击左下角齿轮图标 ⚙️
   - 或使用快捷键 `Cmd + ,` (macOS) / `Ctrl + ,` (Windows/Linux)

2. **进入 Models 设置**
   - 在设置搜索框中输入 "Models"
   - 或直接导航到 "Cursor" → "Models"

3. **添加自定义模型**
   - 点击 **"Add Custom Model"** 按钮
   - 选择 **"OpenAI"** 协议

4. **填写配置信息**
   - **OpenAI API Key**: 粘贴您从智谱平台获取的 API Key
   - **Override OpenAI Base URL**: 
     ```
     https://open.bigmodel.cn/api/coding/paas/v4
     ```
   - **Model Name**: 输入模型名称（注意：必须使用大写）
     - `GLM-4.7` （推荐，最新版本）
     - `GLM-4.6`
     - `GLM-4.5-air`

5. **保存并切换**
   - 点击 "Save" 保存配置
   - 在 Cursor 主页或聊天界面选择刚创建的 **GLM-4.7 Provider**

#### 方法二：通过配置文件（高级）

如果 UI 配置不生效，可以尝试直接修改配置文件：

1. **打开配置文件**
   ```bash
   # macOS
   open ~/Library/Application\ Support/Cursor/User/settings.json
   
   # 或使用编辑器
   code ~/Library/Application\ Support/Cursor/User/settings.json
   ```

2. **添加配置**（需要根据 Cursor 的实际配置格式）
   ```json
   {
     "cursor.customModels": [
       {
         "name": "GLM-4.7",
         "provider": "openai",
         "apiKey": "your-api-key-here",
         "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
         "model": "GLM-4.7"
       }
     ]
   }
   ```

   ⚠️ **注意**：此方法需要确认 Cursor 的实际配置格式，建议优先使用 UI 方法。

### 3. 验证配置

1. 在 Cursor 中打开聊天界面
2. 检查模型选择器，应该能看到 "GLM-4.7" 选项
3. 发送一条测试消息，确认可以正常使用

## 常见问题

### Q1: 提示 "The model GLM does not work with your current plan or api key"
**A**: 这表示您不是 Cursor 高级会员。需要：
- 升级到 Cursor Pro 或更高版本
- 或使用 Cursor 内置的 Claude 模型

### Q2: 模型名称必须大写吗？
**A**: 是的，根据文档，在 Cursor 中必须使用大写模型名称：
- ✅ `GLM-4.7`
- ❌ `glm-4.7`

### Q3: API Key 在哪里获取？
**A**: 
1. 访问 https://open.bigmodel.cn/
2. 登录后进入控制台
3. 在 "API Keys" 部分创建新的 Key

### Q4: 可以使用哪些模型？
**A**: 支持以下模型：
- `GLM-4.7` - 最新版本，推荐使用
- `GLM-4.6` - 上一版本
- `GLM-4.5-air` - 轻量版本

### Q5: Base URL 可以修改吗？
**A**: 不可以，必须使用：
```
https://open.bigmodel.cn/api/coding/paas/v4
```

## 参考链接

- [智谱 AI 开放平台](https://open.bigmodel.cn/)
- [Cursor 配置文档](https://docs.bigmodel.cn/cn/coding-plan/tool/cursor)
- [GLM Coding Plan 套餐](https://open.bigmodel.cn/coding-plan)

## 配置完成后的使用

配置完成后，您可以在 Cursor 中：
- ✅ 使用 GLM-4.7 进行代码生成
- ✅ 使用 GLM-4.7 进行代码调试
- ✅ 使用 GLM-4.7 进行任务分析
- ✅ 享受智谱 AI 的代码编程专享计划

---

**最后更新**: 2025-01-21
**配置状态**: 待配置
