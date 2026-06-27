# AI 集成规划 & 接口预留

> 目标：一期不写一行 AI 代码，但架构上把接口层和数据库留好。二期想加 AI，填个 `.env` 的 API key 就能通。

---

## 一、AI 场景四梯队

| 优先级 | 场景 | 说明 | 状态 |
|--------|------|------|------|
| **P0** | 分流预问诊 | 活动报名前收集用户心理状态，给出初步评估和活动建议 | 第一个做 |
| **P1** | 活动推荐 / 客服 | 基于用户画像智能匹配活动；FAQ 自动答疑 | — |
| **P2** | 情绪陪伴 | 轻量级情绪疏导对话 | ⚠️ 慎碰，涉及心理健康合规 |
| **P3** | 中医体质辨识 | 结合中医体质分类的远期规划 | 远期 |

---

## 二、架构预留

### 2.1 后端骨架：`backend/services/ai_service.py`

MVP 阶段只搭壳，所有方法返回占位数据或 `NotImplementedError`：

```python
class AIService:
    """AI 服务统一入口，二期填 .env 的 API key 即可激活"""

    def __init__(self):
        self.provider = None       # 二期从 .env 读取
        self.model = None
        self.api_key = None

    def chat(self, messages, conversation_id=None):
        """通用对话接口"""
        raise NotImplementedError("AI 服务尚未激活，请在 .env 配置 API key")

    def pre_assessment(self, user_input):
        """分流预问诊 (P0)"""
        raise NotImplementedError

    def recommend_activities(self, user_id):
        """活动推荐 (P1)"""
        raise NotImplementedError

    def emotional_companion(self, user_input, conversation_id):
        """情绪陪伴 (P2)"""
        raise NotImplementedError
```

### 2.2 数据库：`conversations` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 主键 |
| user_id | VARCHAR(64) | 用户 OpenID |
| scene | VARCHAR(32) | 场景：pre_assessment / companion / recommend |
| role | VARCHAR(16) | user / assistant |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间 |

### 2.3 占位 API 路由（4个）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/ai/pre-assessment` | POST | 分流预问诊 |
| `/api/ai/chat` | POST | 通用对话 |
| `/api/ai/recommend` | GET | 活动推荐 |
| `/api/ai/companion` | POST | 情绪陪伴 |

MVP 阶段全部返回 `{"active": false, "message": "AI 服务尚未激活"}`。

---

## 三、协议选型

**直接用 OpenAI 兼容 Chat API，不引入 MCP。**

理由：
- 场景太简单，不需要工具调用 / 多步推理
- 国产模型几乎全部兼容 OpenAI Chat 格式
- 换模型只改 `base_url` + `model` + `api_key`，一行代码不用动

---

## 四、国产模型比价

| 模型 | 价格（元/百万token） | 合规 | 备注 |
|------|----------------------|------|------|
| 智谱 GLM | ~0.1 | ⭐⭐⭐ | 最便宜 |
| 通义千问 | ~0.5 | ⭐⭐⭐⭐⭐ | 合规最好，阿里云生态 |
| DeepSeek | ~0.5 | ⭐⭐⭐⭐ | 性价比高 |
| 百度文心 | ~0.6 | ⭐⭐⭐⭐ | — |

**建议**：生产环境用通义千问（合规优先），开发测试用智谱（省钱）。

---

## 五、成本估算

- 预问诊场景每次 ~500 token 输入 + ~200 token 输出
- 日活 100 人，每人日均 1 次对话
- 月消耗：100 × 30 × 700 token ≈ 210 万 token/月
- 智谱费用：≈ **0.2 元/月**，通义千问：≈ **1 元/月**

---

## 六、二期激活步骤

1. 在 `.env` 添加：
   ```
   AI_PROVIDER=zhipu
   AI_API_KEY=your_key
   AI_MODEL=glm-4-flash
   ```
2. 取消 `ai_service.py` 中各方法的 `raise NotImplementedError`
3. 取消 `routes.py` 中占位 API 的 `active: false` 返回
4. 运行 `migrations.py` 创建 `conversations` 表

完工。
