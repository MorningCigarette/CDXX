import datetime
import json
import os
from datetime import timedelta

import requests
from chinese_calendar import is_workday, is_holiday

# 配置区
APP_ID = os.environ.get("WX_APP_ID")
APP_SECRET = os.environ.get("WX_APP_SECRET")
TEMPLATE_ID = os.environ.get("WX_TEMPLATE_ID")


class ChengduAirBot:
    def get_access_token(self):
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APP_ID}&secret={APP_SECRET}"
        return requests.get(url).json().get("access_token")

    def get_latest_aqi(self):
        """获取昨日AQI实况"""
        yesterday = datetime.datetime.now() - timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d 00:00:00')
        api = "https://xn.prd.sumztech.com:65205/api/airprovinceproduct/app-api/CityPublish/FindAirDay"
        payload = f"timePoint={date_str.replace(' ', '+').replace(':', '%3A')}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        try:
            res = requests.post(api, data=payload, headers=headers).json()
            for city in res.get('result', []):
                if city['name'] == "成都市": return city
            return None
        except:
            return None

    def get_traffic_restriction(self, aqi):
        """限行规则逻辑"""
        now = datetime.datetime.now()
        weekday = now.isoweekday()
        rules = {1: "1和6", 2: "2和7", 3: "3和8", 4: "4和9", 5: "5和0"}

        if is_holiday(now) or not is_workday(now): return "🚗 不限行"

        if aqi > 150:  # 黄色及以上预警
            level = "🟠 橙色/🟡 黄色预警" if aqi <= 200 else "🚫 红色预警"
            time_range = "06:00-22:00" if aqi <= 200 else "全天"
            return f"{level}限行 ({time_range}, 尾号{rules.get(weekday)}, 含小客车及货车)"

        return f"✅ 常规限行 (07:30-20:00, 尾号{rules.get(weekday)})"

    def push(self, token, openid, aqi_data):
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}"
        aqi = int(aqi_data['aqi'])
        traffic = self.get_traffic_restriction(aqi)

        body = {
            "touser": openid,
            "template_id": TEMPLATE_ID,
            "data": {
                "city": {"value": "成都市", "color": "#173177"},
                "aqi": {"value": str(aqi), "color": "#FF0000" if aqi > 100 else "#00FF00"},
                "traffic": {"value": traffic, "color": "#d35400"},
                "date": {"value": datetime.datetime.now().strftime('%Y-%m-%d'), "color": "#173177"},
                "remark": {"value": "\n未来7天预测请点击详情查看。", "color": "#888888"}
            }
        }
        requests.post(url, json=body)

    def run(self):
        aqi_data = self.get_latest_aqi()
        if not aqi_data: return

        with open("subscribers.json", "r") as f:
            users = json.load(f)

        token = self.get_access_token()
        for user in users:
            self.push(token, user, aqi_data)


if __name__ == "__main__":
    ChengduAirBot().run()