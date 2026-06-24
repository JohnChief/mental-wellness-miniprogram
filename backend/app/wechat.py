import threading
import time

import requests
from flask import current_app

_token_lock = threading.Lock()
_token_cache = {"value": "", "expires_at": 0}


class WeChatApiError(RuntimeError):
    pass


def _get_access_token():
    now = time.time()
    if _token_cache["value"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["value"]

    with _token_lock:
        now = time.time()
        if _token_cache["value"] and _token_cache["expires_at"] > now + 60:
            return _token_cache["value"]

        app_id = current_app.config["WECHAT_APP_ID"]
        app_secret = current_app.config["WECHAT_APP_SECRET"]
        if not app_id or not app_secret:
            raise WeChatApiError("服务端尚未配置微信 AppID 和 AppSecret")

        try:
            response = requests.get(
                "https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": app_id,
                    "secret": app_secret,
                },
                timeout=8,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise WeChatApiError("连接微信服务失败，请稍后重试") from exc
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise WeChatApiError(payload.get("errmsg", "获取微信 access_token 失败"))

        _token_cache["value"] = token
        _token_cache["expires_at"] = now + int(payload.get("expires_in", 7200))
        return token


def resolve_phone_number(phone_code):
    if not phone_code:
        raise WeChatApiError("缺少手机号授权凭证")

    access_token = _get_access_token()
    try:
        response = requests.post(
            "https://api.weixin.qq.com/wxa/business/getuserphonenumber",
            params={"access_token": access_token},
            json={"code": phone_code},
            timeout=8,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise WeChatApiError("连接微信服务失败，请稍后重试") from exc
    payload = response.json()
    if payload.get("errcode") != 0:
        raise WeChatApiError(payload.get("errmsg", "手机号授权失败"))

    phone_info = payload.get("phone_info") or {}
    phone = phone_info.get("phoneNumber") or phone_info.get("purePhoneNumber")
    if not phone:
        raise WeChatApiError("微信未返回手机号")
    return phone
