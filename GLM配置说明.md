# GLM (智谱AI) API 配置说明

**配置完成时间**: 2026-02-15 22:23  
**配置人**: 符哥

---

## ✅ 配置完成

### 1. 配置文件更新

已在以下文件中添加GLM配置：

#### `app/core/config.py`
```python
# GLM (智谱AI) 配置
GLM_API_KEY: Optional[str] = None  # GLM API Key
GLM_API_BASE: str = "https://open.bigmodel.cn/api/paas/v4"  # GLM API 基础URL
GLM_MODEL: str = "glm-4"  # 默认模型
GLM_MAX_TOKENS: int = 4000  # 最大生成token数
GLM_TEMPERATURE: float = 0.7  # 温度参数
GLM_TIMEOUT: int = 30  # 请求超时时间（秒）
GLM_ENABLED: bool = False  # 是否启用GLM AI功能
```

#### `.env` (已添加你的API Key)
```bash
# GLM (智谱AI) 配置
GLM_API_KEY=8677faa1d4a54f4bb7d171069e9d84f9.TSMGwqPbEyTx3pja
GLM_ENABLED=true
GLM_MODEL=glm-4
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
```

---

## 📚 使用方法

### 方法一：在代码中使用

```python
from app.core.config import settings
import requests

def call_glm_api(prompt: str):
    """调用GLM API"""
    if not settings.GLM_ENABLED:
        raise ValueError("GLM未启用")
    
    headers = {
        "Authorization": f"Bearer {settings.GLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.GLM_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": settings.GLM_MAX_TOKENS,
        "temperature": settings.GLM_TEMPERATURE
    }
    
    response = requests.post(
        f"{settings.GLM_API_BASE}/chat/completions",
        headers=headers,
        json=data,
        timeout=settings.GLM_TIMEOUT
    )
    
    return response.json()

# 使用示例
result = call_glm_api("你好，请介绍一下智谱AI")
print(result['choices'][0]['message']['content'])
```

### 方法二：创建GLM Service

```python
# app/services/glm_service.py
from typing import Optional
from app.core.config import settings
import requests
import logging

logger = logging.getLogger(__name__)


class GLMService:
    """智谱AI GLM服务"""
    
    def __init__(self):
        self.api_key = settings.GLM_API_KEY
        self.api_base = settings.GLM_API_BASE
        self.model = settings.GLM_MODEL
        self.enabled = settings.GLM_ENABLED
    
    def is_enabled(self) -> bool:
        """检查GLM是否启用"""
        return self.enabled and bool(self.api_key)
    
    def chat(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        调用GLM对话API
        
        Args:
            prompt: 用户输入
            max_tokens: 最大token数（可选）
            temperature: 温度参数（可选）
        
        Returns:
            GLM的回复文本
        """
        if not self.is_enabled():
            raise ValueError("GLM服务未启用或未配置API Key")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens or settings.GLM_MAX_TOKENS,
            "temperature": temperature or settings.GLM_TEMPERATURE
        }
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=settings.GLM_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            logger.error(f"GLM API调用失败: {e}")
            raise


# 使用示例
glm = GLMService()
if glm.is_enabled():
    reply = glm.chat("帮我生成一份项目需求分析报告")
    print(reply)
```

---

## 🎯 在PMS系统中集成GLM

### 场景1：AI辅助报价单生成

```python
# app/api/v1/endpoints/sales/quotes.py
from app.services.glm_service import GLMService

@router.post("/quotes/ai-generate")
def generate_quote_with_ai(
    customer_name: str,
    product_type: str,
    requirements: str,
    db: Session = Depends(get_db)
):
    """AI辅助生成报价单"""
    glm = GLMService()
    
    prompt = f"""
    请根据以下信息生成一份专业的自动化测试设备报价单：
    - 客户：{customer_name}
    - 产品类型：{product_type}
    - 需求描述：{requirements}
    
    报价单应包括：设备配置、技术参数、报价明细、交期说明
    """
    
    ai_quote = glm.chat(prompt)
    
    return {
        "ai_generated_quote": ai_quote,
        "customer": customer_name,
        "product_type": product_type
    }
```

### 场景2：AI辅助技术文档撰写

```python
# app/api/v1/endpoints/engineer_performance/knowledge.py
from app.services.glm_service import GLMService

@router.post("/knowledge/ai-improve")
def improve_document_with_ai(
    document_id: int,
    original_content: str,
    db: Session = Depends(get_db)
):
    """AI辅助改进技术文档"""
    glm = GLMService()
    
    prompt = f"""
    请帮我改进这份技术文档，使其更专业、清晰：
    
    原文：
    {original_content}
    
    请从以下方面改进：
    1. 逻辑结构优化
    2. 专业术语准确性
    3. 可读性提升
    4. 补充必要的技术细节
    """
    
    improved_content = glm.chat(prompt, max_tokens=8000)
    
    return {
        "original": original_content,
        "improved": improved_content
    }
```

### 场景3：AI智能问答（项目管理助手）

```python
# app/api/v1/endpoints/ai_assistant.py
from app.services.glm_service import GLMService

@router.post("/ai/ask")
def ai_assistant(
    question: str,
    context: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """AI项目管理助手"""
    glm = GLMService()
    
    # 构建上下文提示
    system_context = """
    你是金凯博自动化测试设备公司的项目管理助手。
    你熟悉ICT、FCT、AOI等测试设备的项目管理流程。
    请基于专业知识回答用户的问题。
    """
    
    full_prompt = f"{system_context}\n\n用户问题：{question}"
    if context:
        full_prompt += f"\n\n相关上下文：{context}"
    
    answer = glm.chat(full_prompt)
    
    return {
        "question": question,
        "answer": answer
    }
```

---

## 🔧 配置参数说明

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `GLM_API_KEY` | API密钥 | None | 你的API Key |
| `GLM_ENABLED` | 是否启用 | False | true/false |
| `GLM_MODEL` | 模型名称 | glm-4 | glm-4, glm-4v, glm-3-turbo |
| `GLM_API_BASE` | API基础URL | https://open.bigmodel.cn/api/paas/v4 | - |
| `GLM_MAX_TOKENS` | 最大token数 | 4000 | 100-8000 |
| `GLM_TEMPERATURE` | 温度参数 | 0.7 | 0.0-1.0 |
| `GLM_TIMEOUT` | 超时时间(秒) | 30 | 10-60 |

---

## 🔐 安全建议

1. **不要提交API Key到Git**
   - `.env` 文件已在 `.gitignore` 中
   - 生产环境使用环境变量或密钥管理服务

2. **API Key轮转**
   - 定期更换API Key
   - 智谱AI控制台可以生成新Key

3. **调用频率控制**
   - 建议添加缓存机制
   - 避免同一问题重复调用

---

## 📊 费用说明

智谱AI GLM-4 计费方式（以官网为准）：
- **GLM-4**: 约 ¥0.1/千tokens（输入）+ ¥0.1/千tokens（输出）
- **GLM-3-Turbo**: 约 ¥0.005/千tokens（更便宜）

**成本控制建议**：
- 开发/测试环境使用 GLM-3-Turbo
- 生产环境根据实际需求选择模型
- 设置 `GLM_MAX_TOKENS` 限制单次消耗

---

## 🧪 测试配置

### 快速测试

```bash
# 测试API连通性
curl -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Authorization: Bearer 8677faa1d4a54f4bb7d171069e9d84f9.TSMGwqPbEyTx3pja" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4",
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

### Python测试脚本

```python
# test_glm.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GLM_API_KEY")
api_base = os.getenv("GLM_API_BASE")

response = requests.post(
    f"{api_base}/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "glm-4",
        "messages": [
            {"role": "user", "content": "你好，请简单介绍你自己"}
        ]
    }
)

print(response.json())
```

---

## 🔍 常见问题

### Q: API Key失效怎么办？
A: 登录智谱AI控制台重新生成，然后更新 `.env` 文件

### Q: 如何切换模型？
A: 修改 `.env` 中的 `GLM_MODEL` 参数：
```bash
GLM_MODEL=glm-3-turbo  # 更快更便宜
# 或
GLM_MODEL=glm-4v  # 支持视觉理解
```

### Q: 调用失败如何排查？
A: 检查以下几点：
1. API Key是否正确
2. 网络是否通畅
3. 余额是否充足
4. 请求格式是否正确

---

## 📖 参考文档

- [智谱AI官方文档](https://open.bigmodel.cn/dev/api)
- [GLM-4 模型介绍](https://open.bigmodel.cn/dev/howuse/model)
- [API接口说明](https://open.bigmodel.cn/dev/api#overview)

---

**配置完成！** ✅

符哥，你的GLM API Key已成功配置到系统中。可以开始在代码中使用了！

如需帮助集成到具体功能，随时告诉我！💪🐾
