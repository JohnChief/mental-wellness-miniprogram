# 心语轻疗愈小程序

原生微信小程序 + Flask + MySQL 的活动报名 MVP，部署目标为微信云托管。

## 项目结构

```text
.
├── pages/              原生小程序页面
├── utils/api.js        云托管 API 封装
├── utils/mock.js       未部署后端时的预览数据
├── config.js           环境与服务配置
├── backend/            Flask 云托管服务
└── docs/               产品、架构与上线资料
```

当前配置：

- 云开发环境：`prod-d6g7im3ft632062b9`
- 云托管服务：`flask-ytaf`
- 数据库：MySQL，默认库名 `flask_demo`

## 本地预览

用微信开发者工具打开仓库根目录。`config.js` 默认开启 `useMock: true`，无需后端即可预览主要页面和报名流程。

## 接入真实后端

1. 按 [backend/README.md](backend/README.md) 部署 `backend` 目录。
2. 在云端调试验证 `GET /health`。
3. 将 `config.js` 中的 `useMock` 改为 `false`。
4. 在开发者工具中测试首页、活动详情、报名、我的报名和注销。

## 当前范围

已完成用户端 MVP 与后端核心 API。管理接口已具备，正式管理界面、微信手机号快捷授权、动态二维码签到和正式运营素材留待下一阶段。
