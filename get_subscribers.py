import json
import os

import requests

APP_ID = os.environ.get("WX_APP_ID")
APP_SECRET = os.environ.get("WX_APP_SECRET")


def update_subscribers():
    # 获取 Token
    token_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
    token = requests.get(token_url).json().get("access_token")

    if not token:
        print("❌ 获取 Token 失败，请检查 AppID 和 Secret")
        return

    # 获取关注者列表
    list_url = f"https://api.weixin.qq.com/cgi-bin/user/get?access_token={token}"
    res = requests.get(list_url).json()

    if "data" in res and "openid" in res["data"]:
        openids = res["data"]["openid"]
        with open("subscribers.json", "w") as f:
            json.dump(openids, f, indent=4)
        print(f"✅ 成功同步 {len(openids)} 名订阅者")
    else:
        print("📭 暂无关注者")
        with open("subscribers.json", "w") as f:
            json.dump([], f)


if __name__ == "__main__":
    update_subscribers()