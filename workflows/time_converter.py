import sys
import time
import json
from datetime import datetime, timezone, timedelta

# 定义北京时间时区
beijing_tz = timezone(timedelta(hours=8))

def timestamp_to_date(timestamp):
    if len(timestamp) == 13:  # 如果时间戳是 13 位，转换成 10 位
        timestamp = timestamp[:-3]
    # 转换为北京时间
    return datetime.fromtimestamp(int(timestamp), beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

def date_to_timestamp(date_str):
    # 将输入的日期字符串按北京时间解析
    dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    # 加上北京时间时区
    dt = dt.replace(tzinfo=beijing_tz)
    # 转换为 UTC 时间戳，返回秒级时间戳
    return int(dt.timestamp())

def main(query):
    # 初始化结果
    items = []

    # 如果输入为空时，提示使用方法
    if not query:
        items.append({
            "title": "请输入时间戳或日期格式",
            "subtitle": "例如：df 1633036800 或者 df 2021-10-01 00:00:00",
            "valid": False
        })
    else:
        # 默认转换逻辑
        if query == "now":
            # 获取当前北京时间的时间戳
            result = int(datetime.now(beijing_tz).timestamp())
        elif query.isdigit() and (len(query) == 10 or len(query) == 13):  # 输入是时间戳
            result = timestamp_to_date(query)
        else:
            try:  # 尝试将输入解析为日期
                result = str(date_to_timestamp(query))
            except ValueError:
                result = "Invalid input"

        # 添加结果项到 Script Filter
        items.append({
            "title": f"结果: {result}",
            "subtitle": "按回车复制到剪贴板",
            "arg": result,  # 回车后会传递这个字段
            "valid": True
        })

    # 返回 JSON 格式内容供 Alfred 渲染
    print(json.dumps({"items": items}))

if __name__ == "__main__":
    query = " ".join(sys.argv[1:])  # 获取输入内容
    main(query)
