# 飞书长连接 AI 机器人

这个目录是一个最小可运行版本：

```text
飞书群里 @ 机器人
  -> 本地长连接进程收到消息
  -> 调用 OpenAI
  -> 机器人把回复发回飞书
```

## 1. 准备飞书后台

确认已经完成：

- 事件订阅方式选择「使用长连接接收事件」
- 权限已开通：
  - `im:message`
  - `im:message:readonly`
  - `im:message:send_as_bot`
  - 群聊 @ 机器人消息相关 readonly 权限
  - 私聊机器人消息 readonly 权限
- 事件已订阅：
  - `im.message.receive_v1`
- 应用已发布版本并安装到企业
- 机器人已被拉进目标群聊

## 2. 配置密钥

复制示例配置：

```powershell
Copy-Item feishu_bot\.env.example feishu_bot\.env
```

然后编辑 `feishu_bot/.env`：

```text
FEISHU_APP_ID=你的飞书 App ID
FEISHU_APP_SECRET=你的飞书 App Secret
OPENAI_API_KEY=你的 OpenAI API Key
OPENAI_MODEL=gpt-4.1-mini
```

不要把 `.env` 提交到 Git。

## 3. 安装依赖

请使用你已经安装 `lark-oapi` 的 Python 环境。

```powershell
pip install -r feishu_bot\requirements.txt
```

如果 `python` 不在 PATH，先用下面命令找你的解释器：

```powershell
py -0p
```

然后用对应解释器运行，例如：

```powershell
py -3 -m pip install -r feishu_bot\requirements.txt
```

## 4. 启动机器人

```powershell
python feishu_bot\bot.py
```

或：

```powershell
py -3 feishu_bot\bot.py
```

看到类似 `Feishu bot started` 后，到飞书群里 @ 机器人发消息。

## 5. 使用建议

为了避免多个 AI 在群里互相无限回复，当前代码只处理：

- 私聊机器人消息
- 群里明确 @ 机器人的消息

如果消息来自机器人，或者内容为空，会直接忽略。
