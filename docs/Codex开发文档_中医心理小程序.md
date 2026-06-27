# Codex 开发文档 — 中医心理小程序

> 心语轻疗愈小程序完整开发手册。新人拿到这份文档即可了解项目全貌和开发规范。
> 最后更新：2026-06-27

---

## 第一章 项目概述

心语轻疗愈小程序是一个心理健康活动报名平台，核心验证用户浏览活动 → 报名 → 管理端处理报名的完整流程。

- **小程序 AppID**：`wxbe032d60211a517d`
- **云开发环境**：`prod-d6g7im3ft632062b9`
- **云托管服务**：`flask-ytaf`
- **部署目标**：微信云托管

---

## 第二章 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | 原生微信小程序 | WXML + WXSS + JS |
| 后端 | Flask (Python) | 部署于微信云托管 |
| 数据库 | MySQL | 云托管数据库，库名 `flask_demo` |
| 管理端 | Flask Jinja2 模板 | 同仓 `/admin` 路由 |
| AI 机器人 | 飞书长连接 | `feishu_bot/bot.py`，OpenAI 兼容 API |

---

## 第三章 项目结构

```
mental-wellness-miniprogram/
├── pages/                    # 小程序页面
│   ├── index/                # 首页（品牌卡+主推活动+服务标签）
│   ├── activity/             # 活动列表（筛选：全部/本周/免费/线下）
│   ├── activityDetail/       # 活动详情（文案+报名入口）
│   ├── registration/         # 报名页（姓名+手机+备注+隐私勾选）
│   ├── mine/                 # 我的（登录/资料编辑/注销/协议入口）
│   ├── records/              # 报名记录（已报名/已签到/已取消+取消操作）
│   └── agreement/            # 协议（隐私政策/用户协议/免责声明/注销说明）
├── utils/
│   ├── api.js                # 云托管 API 封装
│   └── mock.js               # 离线预览数据
├── config.js                 # 环境与服务配置
├── backend/                  # Flask 后端
│   ├── app/
│   │   ├── __init__.py       # 应用工厂
│   │   ├── routes.py         # API 路由
│   │   ├── models.py         # 数据模型
│   │   ├── admin.py          # 管理后台
│   │   ├── config.py         # 配置管理
│   │   ├── extensions.py     # Flask 扩展
│   │   ├── serializers.py    # 序列化
│   │   ├── wechat.py         # 微信登录
│   │   ├── migrations.py     # 数据库迁移
│   │   └── seed.py           # 测试数据
│   └── tests/                # 测试
├── feishu_bot/               # 飞书 AI 机器人
├── docs/                     # 项目文档
└── Dockerfile                # 云托管部署
```

---

## 第四章 数据模型

详见 `docs/数据库表结构.md`。实际使用 5 张表：

| 表 | 用途 | 关键字段 |
|----|------|----------|
| `users` | 微信用户 | openid(UK), nickname, phone, is_vip, privacy_consent_at, deleted_at |
| `events` | 活动 | title, event_time, status(online/offline), is_featured, capacity |
| `registrations` | 报名记录 | event_id+user_id(唯一), status(registered/checked_in/cancelled) |
| `settings` | 平台配置 | key/value(JSON), 首页名称/标语/服务标签 |
| `admin_audits` | 操作审计 | action, target_type, target_id, detail |

**注意**：当前 MVP 没有 `admin_users` 表，管理员通过环境变量 `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH` 认证。

---

## 第五章 API 路由

所有 API 返回格式：`{"code": 0, "data": ...}` 或 `{"code": 1, "message": "..."}`。

### 小程序端 API（无需鉴权头）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | 健康检查（含DB连接测试） |
| `/api/home` | GET | 首页数据（平台信息+主推活动+活动列表） |
| `/api/events` | GET | 活动列表，支持 `?filter=全部/本周/免费/线下` |
| `/api/events/<id>` | GET | 活动详情（含描述/适合人群/流程/注意事项） |
| `/api/auth/me` | GET | 当前用户状态，未注册返回 `{registered: false}` |
| `/api/auth/register` | POST | 注册（昵称/头像/手机号code/隐私版本） |
| `/api/auth/profile` | PUT | 更新个人资料（需已注册） |

### 小程序端 API（需已注册，通过 X-WX-OPENID 识别）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/registrations` | POST | 提交报名（含名额事务锁+重复报名检测+截止时间检测） |
| `/api/registrations/mine` | GET | 我的报名列表 |
| `/api/registrations/<id>/cancel` | PUT | 取消报名（已签到不可取消） |
| `/api/account` | DELETE | 注销账号（匿名化资料+替换OpenID） |

### Admin API（需 X-ADMIN-KEY 头）

| 路由 | 方法 | 说明 |
|------|------|------|
| `/admin/api/events` | GET | 活动全列表（含状态） |
| `/admin/api/events` | POST | 创建活动 |
| `/admin/api/events/<id>` | PUT | 更新活动 |
| `/admin/api/events/<id>/toggle` | PUT | 上下架切换 |
| `/admin/api/registrations` | GET | 报名列表，支持 `?event_id=` |
| `/admin/api/registrations/<id>/checkin` | POST | 签到 |
| `/admin/api/users` | GET | 用户列表 |
| `/admin/api/users/<id>/vip` | PUT | 切换单个VIP |

---

## 第六章 认证流程

当前 MVP 使用微信云托管自动注入的 `X-WX-OPENID` 请求头识别用户。

```
小程序端（wx.cloud.callContainer）
  |
  | 微信云托管自动注入 X-WX-OPENID 头
  v
后端 Flask
  |
  | GET /api/auth/me  →  返回用户信息或 {registered: false}
  | POST /api/auth/register  →  创建用户（昵称+头像+隐私同意）
  |
  v
后续请求自动携带 X-WX-OPENID → require_user 装饰器校验
```

关键安全原则：
- 前端**不**自行发送 OpenID，只信任云托管注入的请求头
- 昵称和头像可选，手机号在报名时手动填写
- 开发环境可通过 `ALLOW_DEV_OPENID=true` + `X-DEV-OPENID` 头本地调试
- 注销时将 OpenID 替换为 `deleted-{id}-{timestamp}`，保留匿名化记录

---

## 第七章 本地开发

1. 用微信开发者工具打开仓库根目录
2. 后端：
   ```bash
   cd backend
   pip install -r requirements.txt
   python run.py
   ```
3. 如需离线预览，将 `config.js` 中 `useMock` 改为 `true`
4. 接入真实后端后改回 `false`

---

## 第八章 部署

### 云托管部署

1. 将 `backend/` 目录部署到云托管服务 `flask-ytaf`
2. 配置环境变量（数据库连接、微信 AppSecret 等）
3. 验证 `GET /health`
4. 小程序配置服务器域名白名单

### Docker

```bash
docker build -t mental-wellness .
docker run -p 5000:5000 --env-file .env mental-wellness
```

---

## 第九章 管理后台

访问 `/admin/login` 进入运营管理后台（Jinja2 模板渲染）。

### 功能总览
- **数据概览**：活动数/在线数/报名数/待签到数/用户数/VIP数 + 近期报名 + 近期活动
- **活动管理**：新建/编辑/上下架，支持封面图片上传（jpg/png/gif/webp）
- **报名管理**：按活动/状态/关键词筛选，签到、测试数据重置
- **用户管理**：搜索/排序（最新/最旧/昵称/VIP优先）、VIP筛选、单个/批量设置VIP
- **测试工具**：受 `ADMIN_TEST_TOOLS_ENABLED` 保护，可生成8位测试用户+6条报名

### 安全
- Session 登录（`flask.session`）+ 限速（5次失败锁15分钟）
- CSRF 保护（`csrf_token` 表单域校验）
- 编辑活动时乐观锁（`updated_at` 版本号校验防冲突）
- Toast 操作反馈 + 不可逆操作二次确认
- `secure_filename` 上传过滤 + Magic bytes 图片校验
- `X-Content-Type-Options` / `X-Frame-Options` / `Referrer-Policy` 安全头

### 认证方式
当前单管理员，通过环境变量认证：
- `ADMIN_USERNAME` + `ADMIN_PASSWORD_HASH`（Werkzeug 哈希）
- 开发期可临时用 `ADMIN_PASSWORD` 明文密码
- 多管理员角色留待后续

---

## 第十章 合规底线

MVP 阶段保留：
- 报名前必须勾选同意隐私政策和用户协议
- 只收集完成报名所必需的信息
- 后端日志不打印手机号、openid、报名详情
- 管理端必须登录后才能访问用户数据
- 隐私政策、用户协议、免责声明在小程序内可访问

后续补充：
- 账号注销（已实现）
- 数据导出
- 手机号脱敏展示
- 多角色权限

---

## 第十一章 飞书 AI 机器人

详见 `feishu_bot/README.md`。

架构：
```
飞书群 @机器人 → 长连接接收 → 调用 OpenAI API → 回复发回飞书
```

配置：
- 飞书 App ID / Secret
- OpenAI 兼容 API Key / Model
- 只处理私聊和明确 @ 的消息，避免 AI 互聊

---

## 第十二章 AI 功能接口预留

> 一期不写一行 AI 代码。但架构上把接口层和数据库留好，二期填个 `.env` API key 就能通。

### 三件 MVP 必须做的事

#### 1. 建 `backend/services/ai_service.py` 骨架

```python
# backend/services/ai_service.py
class AIService:
    """AI 服务统一入口"""

    def __init__(self):
        self.provider = None
        self.model = None
        self.api_key = None

    def chat(self, messages, conversation_id=None):
        raise NotImplementedError("AI 服务尚未激活")

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

#### 2. 建 `conversations` 数据库集合

```sql
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    scene VARCHAR(32) NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_scene (user_id, scene)
);
```

#### 3. 注册 4 个占位 API 路由

| 路由 | 方法 | 场景 |
|------|------|------|
| `/api/ai/pre-assessment` | POST | 分流预问诊 |
| `/api/ai/chat` | POST | 通用对话 |
| `/api/ai/recommend` | GET | 活动推荐 |
| `/api/ai/companion` | POST | 情绪陪伴 |

MVP 阶段全部返回：
```json
{"active": false, "message": "AI 服务尚未激活，请在 .env 配置 API key"}
```

### AI 场景规划

| 优先级 | 场景 | 状态 |
|--------|------|------|
| P0 | 分流预问诊 | 第一个做 |
| P1 | 活动推荐 / 客服 | — |
| P2 | 情绪陪伴 | ⚠️ 慎碰，涉及心理健康合规 |
| P3 | 中医体质辨识 | 远期 |

### 模型选型

- **协议**：OpenAI 兼容 Chat API（不引入 MCP）
- **生产**：通义千问（合规优先）
- **开发**：智谱 GLM（最便宜，0.1元/百万token）
- **成本**：日活 100 人 ≈ 几块钱/月

### 二期激活

1. `.env` 添加 `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL`
2. 取消 `ai_service.py` 中 `raise NotImplementedError`
3. 取消占位 API 的 `active: false` 返回
4. 运行迁移创建 `conversations` 表

详细规划见：`docs/AI集成规划_接口预留.md`

---

## 附录

### 相关文档
- [README.md](../README.md) — 项目总览
- [MVP架构与上线清单.md](./MVP架构与上线清单.md)
- [数据库表结构.md](./数据库表结构.md)
- [AI集成规划_接口预留.md](./AI集成规划_接口预留.md)
- [backend/README.md](../backend/README.md) — 后端部署
- [feishu_bot/README.md](../feishu_bot/README.md) — 飞书机器人

### Git 分支
- `main` — 主分支
- `codex/*` — Codex 开发分支家族
