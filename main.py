import datetime
import hashlib
import json
import os
from datetime import timedelta

import requests
from chinese_calendar import is_workday, is_holiday
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ================= 配置区 =================
SEND_KEY = os.environ.get("SEND_KEY")  # Server酱 SendKey
STATUS_FILE = "chengdu_air_status.json"

# API配置
TODAY_AQI_API = "https://xn.prd.sumztech.com:65205/api/airprovinceproduct/app-api/CityPublish/FindAirDay"
FORECAST_API = "https://xn.prd.sumztech.com:65205/api/south-west/magic/artificial_forecast/city/list"

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://sthjt.sc.gov.cn',
    'Referer': 'https://sthjt.sc.gov.cn/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"'
}


# ==========================================

class ChengduAirBot:
    def __init__(self):
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_yesterday_aqi(self):
        """获取昨天的实况数据（timePoint 为昨日零点）"""
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        date_str = yesterday.strftime('%Y-%m-%d 00:00:00')
        payload = f"timePoint={date_str.replace(' ', '+').replace(':', '%3A')}"

        try:
            headers = HEADERS.copy()
            headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
            response = self.session.post(TODAY_AQI_API, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('success') and 'result' in data:
                for city in data['result']:
                    if city['name'] == "成都市":
                        return city, yesterday
            return None, yesterday
        except Exception as e:
            print(f"获取实况异常: {e}")
            return None, yesterday

    def get_forecast(self):
        """获取预测数据"""
        try:
            response = self.session.get(FORECAST_API, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('ret') == 0 and 'data' in data:
                for city in data['data']:
                    if city['cityName'] == "成都市":
                        return city
            return None
        except Exception as e:
            print(f"获取预测异常: {e}")
            return None

    def get_traffic_restriction(self, aqi_value, date_obj):
        """
        成都市限行规则计算：
        修正：黄色和橙色预警下，统一限行时间段为 06:00-22:00
        """
        weekday = date_obj.isoweekday()
        normal_rules = {1: "1 和 6", 2: "2 和 7", 3: "3 和 8", 4: "4 和 9", 5: "5 和 0"}

        try:
            # 节假日不限行判断
            if is_holiday(date_obj) or not is_workday(date_obj):
                return "🚗 **不限行**（节假日或周末）"
        except:
            if weekday in [6, 7]: return "🚗 **不限行**（周末）"

        warning = self.get_warning_level(aqi_value)

        if warning == "红色预警":
            return "🚫 **红色预警限行**\n  - **时间**: 全天 24 小时\n  - **规则**: 实行单双号限行"

        elif warning == "橙色预警":
            return (f"🟠 **橙色预警限行**\n"
                    f"  - **时间**: **06:00 - 22:00**\n"
                    f"  - **范围**: 四环路(绕城)以内区域道路\n"
                    f"  - **规则**: 小客车(尾号 {normal_rules.get(weekday)})及货车均限行")

        elif warning == "黄色预警":
            return (f"🟡 **黄色预警限行**\n"
                    f"  - **时间**: **06:00 - 22:00**\n"
                    f"  - **范围**: 四环路(绕城)以内区域道路\n"
                    f"  - **规则**: 小客车(尾号 {normal_rules.get(weekday)})及货车均限行")

        # 常规工作日限行
        return (f"✅ **常规尾号限行**\n"
                f"  - **时间**: 07:30 - 20:00\n"
                f"  - **规则**: 尾号 {normal_rules.get(weekday)} 限行")

    def get_warning_level(self, aqi):
        """根据AQI判断预警级别"""
        if aqi <= 100: return "无"
        if aqi <= 150: return "黄色预警"
        if aqi <= 200: return "橙色预警"
        return "红色预警"

    def get_emoji(self, aqi):
        if aqi <= 50: return "🟢 优"
        if aqi <= 100: return "🟡 良"
        if aqi <= 150: return "🟠 轻度"
        if aqi <= 200: return "🔴 中度"
        return "🟣 重度"

    def send_wechat(self, chengdu_now, forecast, date_obj):
        """发送汇总消息"""
        aqi_val = int(chengdu_now['aqi'])
        data_date = date_obj.strftime('%Y-%m-%d')

        next_day = date_obj + timedelta(days=1)
        next_day_str = next_day.strftime('%Y-%m-%d')

        title = f"🐼 成都空气质量及限行日报 ({next_day_str})"

        # 1. 实况部分
        desp = f"### 📊 成都实况数据 (数据来源于：{data_date})\n"
        desp += f"- **AQI指数**: `{aqi_val}` ({self.get_emoji(aqi_val)})\n"
        desp += f"- **首要污染物**: `{chengdu_now['pollu']}`\n\n"

        # 2. 限行政策部分 (包含详细时间段)
        desp += f"### 🚗 今日限行规定\n"
        desp += f"{self.get_traffic_restriction(aqi_val, datetime.datetime.now())}\n\n"

        # 3. 预测部分 - 修改处：新增“星期”列
        if forecast and 'forecastTime' in forecast:
            desp += "### 📈 未来7天趋势预测\n"
            desp += "| 日期 | 星期 | AQI范围 | 等级 | 污染物 |\n"
            desp += "| :--- | :--- | :--- | :--- | :--- |\n"

            # 星期映射表
            week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

            for i in range(len(forecast['forecastTime'])):
                dt_obj = datetime.datetime.fromtimestamp(forecast['forecastTime'][i] / 1000)
                dt_str = dt_obj.strftime('%m-%d')
                week_str = week_map[dt_obj.weekday()]  # 获取星期

                desp += f"| {dt_str} | {week_str} | {forecast['aqiMin'][i]}-{forecast['aqiMax'][i]} | {forecast['aqiLevel'][i]} | {forecast['primaryPollutant'][i]} |\n"

        desp += f"\n---\n*数据源: 四川省生态环境厅*\n*统计时间: {datetime.datetime.now().strftime('%H:%M:%S')}*"

        post_url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
        res = requests.post(post_url, data={"title": title, "desp": desp})
        return res.status_code == 200

    def check_idempotency(self, aqi_data):
        """检查数据是否有更新"""
        current_hash = hashlib.md5(json.dumps(aqi_data, sort_keys=True).encode()).hexdigest()
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r") as f:
                if json.load(f).get("hash") == current_hash:
                    return False
        with open(STATUS_FILE, "w") as f:
            json.dump({"hash": current_hash}, f)
        return True

    def run(self):
        chengdu_now, date_obj = self.get_yesterday_aqi()
        if not chengdu_now: return
        forecast = self.get_forecast()
        if self.check_idempotency(chengdu_now):
            self.send_wechat(chengdu_now, forecast, date_obj)


if __name__ == "__main__":
    ChengduAirBot().run()