import akshare as ak
import pandas as pd
import requests
import json
from datetime import datetime
from typing import Dict, Any

def get_southbound_flow() -> float:
    """获取南下资金实时净流入数据（东方财富）"""
    try:
        url = "https://push2.eastmoney.com/api/qt/kamtbs.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&ut=b2884a393a59ad64002292a3e90d46a5"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://data.eastmoney.com/hsgt/",
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        data = json.loads(response.text)
        print("南向资金原始数据:", json.dumps(data, indent=2, ensure_ascii=False))
        
        if 'data' in data:
            # 获取南向资金净流入
            total_flow = float(data['data'].get('sh2hk', 0) + data['data'].get('sz2hk', 0)) / 100000000  # 转换为亿元
            print(f"南向资金解析: 总计={total_flow:.2f}亿")
            return total_flow
        return 0.0
    except Exception as e:
        print(f"获取南下资金数据失败: {str(e)}")
        return 0.0

def get_hstech_index() -> Dict[str, float]:
    """获取恒生科技指数实时数据（新浪财经）"""
    try:
        url = "https://hq.sinajs.cn/list=hkHSTECH"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "http://finance.sina.com.cn"
        }
        response = requests.get(url, headers=headers)
        print("恒生科技指数原始数据:", response.text)
        
        # 解析数据，格式：var hq_str_hkHSTECH="HSTECH,恒生科技指数,当前价,昨收,今开,最高,最低..."
        data = response.text.split('=')[1].strip('"').split(',')
        
        price = float(data[2])  # 当前价
        pre_close = float(data[3])  # 昨收价
        change_pct = (price - pre_close) / pre_close * 100  # 计算涨跌幅
        
        print(f"恒生科技指数解析: 当前价={price:.2f}, 昨收={pre_close:.2f}, 涨跌幅={change_pct:.2f}%")
        
        return {
            'price': round(price, 2),
            'change_pct': round(change_pct, 2)
        }
    except Exception as e:
        print(f"获取恒生科技指数数据失败: {str(e)}")
        return {'price': 0.0, 'change_pct': 0.0}

def run() -> Dict[str, Any]:
    """主函数"""
    print("\n开始获取数据...")
    # 获取数据
    southbound_flow = get_southbound_flow()
    hstech_data = get_hstech_index()
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 准备中文展示结果
    result = {
        "type": "market_monitor",
        "data": {
            "时间": current_time,
            "南向资金": f"{southbound_flow:.2f}亿",
            "恒生科技指数": {
                "价格": f"{hstech_data['price']:.2f}",
                "涨跌幅": f"{hstech_data['change_pct']:+.2f}%"  # 添加正负号
            }
        }
    }
    print("\n最终结果:", json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    result = run() 