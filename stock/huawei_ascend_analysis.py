from stock_utils import StockUtils
import requests
import json
from typing import List, Dict
import time
from datetime import datetime
import pandas as pd

class HuaweiAscendAnalyzer:
    def __init__(self):
        self.stock_utils = StockUtils()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 华为昇腾概念股代码列表（示例，需要定期更新）
        self.concept_stocks = self._get_concept_stocks()

    def _get_concept_stocks(self) -> List[str]:
        """获取华为昇腾概念股列表"""
        # 直接返回华为昇腾概念相关股票代码
        return [
            '688256',  # 寒武纪
            '688521',  # 芯原股份
            '300474',  # 景嘉微
            '300223',  # 北京君正
            '688536',  # 思瑞浦
            '002180',  # 纳思达
            '002649',  # 博彦科技
            '688008',  # 澜起科技
            '300458',  # 全志科技
            '688123'   # 聚辰股份
        ]

    def _get_market_sentiment(self, stock_code: str) -> float:
        """计算市场情绪得分（0-100）"""
        try:
            url = 'http://push2his.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': f"{'1' if stock_code.startswith('6') or stock_code.startswith('688') else '0'}.{stock_code}",
                'fields': 'f43,f44,f45,f46,f47,f48,f50,f51,f52,f53',  # 成交量、委比、量比等指标
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fltt': '2',
                'cb': 'jQuery.jQuery' + str(int(time.time() * 1000))
            }
            response = requests.get(url, params=params, headers=self.headers)

            # 处理JSONP响应
            data_text = response.text
            json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
            data = json.loads(json_str)

            if 'data' not in data or not data['data']:
                return 0

            stock_data = data['data']

            # 计算情绪得分（示例算法）
            volume_ratio = float(stock_data.get('f50', 100)) / 100  # 量比
            commission_ratio = float(stock_data.get('f48', 0))  # 委比

            # 简单的情绪计算公式
            sentiment = min(100, max(0, (volume_ratio * 20 + (commission_ratio + 100) / 2) / 2))
            return round(sentiment, 2)

        except Exception as e:
            print(f"获取市场情绪时出错: {str(e)}")
            return 0

    def _get_volume_change_rate(self, stock_code: str) -> float:
        """计算最近5分钟成交量变化率"""
        try:
            url = f"http://push2his.eastmoney.com/api/qt/stock/trends2/get"
            params = {
                'secid': f"{'1' if stock_code.startswith('6') or stock_code.startswith('688') else '0'}.{stock_code}",
                'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11',
                'fields2': 'f51,f53',
                'ndays': 1,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fltt': '2',
                'cb': 'jQuery.jQuery' + str(int(time.time() * 1000))
            }

            response = requests.get(url, params=params, headers=self.headers)

            # 处理JSONP响应
            data_text = response.text
            json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
            data = json.loads(json_str)

            if 'data' not in data or 'trends' not in data['data']:
                return 0

            trends = data['data']['trends']
            if len(trends) < 6:
                return 0

            # 获取最近6个时间点的成交量数据
            recent_volumes = [float(trend.split(',')[1]) for trend in trends[-6:]]

            # 计算变化率
            avg_volume_before = sum(recent_volumes[:-1]) / 5
            current_volume = recent_volumes[-1]

            if avg_volume_before == 0:
                return 0

            change_rate = ((current_volume - avg_volume_before) / avg_volume_before) * 100
            return round(change_rate, 2)

        except Exception as e:
            print(f"计算成交量变化率时出错: {str(e)}")
            return 0

    def analyze_stocks(self):
        """分析所有华为昇腾概念股"""
        results = []

        for stock_code in self.concept_stocks:
            try:
                stock_info = self.stock_utils.get_stock_info(stock_code)
                if 'error' in stock_info:
                    continue

                # 获取市值信息
                url = f"http://push2his.eastmoney.com/api/qt/stock/get"
                params = {
                    'secid': f"{'1' if stock_code.startswith('6') or stock_code.startswith('688') else '0'}.{stock_code}",
                    'fields': 'f116',  # 市值信息
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                    'fltt': '2',
                    'cb': 'jQuery.jQuery' + str(int(time.time() * 1000))
                }
                response = requests.get(url, params=params, headers=self.headers)

                # 处理JSONP响应
                data_text = response.text
                json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
                data = json.loads(json_str)

                if 'data' in data and data['data']:
                    market_value = float(data['data'].get('f116', 0)) / 100000000  # 转换为亿元
                else:
                    market_value = 0

                # 获取成交量变化率
                volume_change = self._get_volume_change_rate(stock_code)

                results.append({
                    'code': stock_code,
                    'name': stock_info['name'],
                    'price': stock_info['price'] * 1000,
                    'change_percent': stock_info['change_percent'] * 100,
                    'market_value': market_value,
                    'sentiment': self._get_market_sentiment(stock_code),
                    'volume_change_rate': volume_change
                })

                # 避免请求过于频繁
                time.sleep(0.5)

            except Exception as e:
                print(f"处理股票 {stock_code} 时出错: {str(e)}")
                continue

        if not results:
            print("未获取到任何股票数据")
            return

        # 转换为DataFrame并排序
        df = pd.DataFrame(results)

        if len(df) > 0:
            df = df.sort_values('market_value')

            # 打印分析结果
            print("\n=== 华为昇腾概念股分析报告 ===")
            print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"共获取到 {len(df)} 只股票")

            if len(df) >= 5:
                print("\n--- 小市值股票（前5名）---")
                self._print_stock_info(df.head())

                print("\n--- 大市值股票（前5名）---")
                self._print_stock_info(df.tail())

                print("\n--- 市场情绪最高的股票（前5名）---")
                self._print_stock_info(df.nlargest(5, 'sentiment'))

                print("\n--- 成交量变化最大的股票（前5名）---")
                self._print_stock_info(df.nlargest(5, 'volume_change_rate'))
            else:
                print("\n--- 所有股票信息 ---")
                self._print_stock_info(df)
        else:
            print("未获取到有效的股票数据")

    def _print_stock_info(self, df: pd.DataFrame):
        """格式化打印股票信息"""
        for _, row in df.iterrows():
            print(f"\n股票代码: {row['code']} ({row['name']})")
            print(f"当前价格: {row['price']:.2f}元")
            print(f"涨跌幅: {row['change_percent']:.2f}%")
            print(f"市值: {row['market_value']:.2f}亿元")
            print(f"市场情绪: {row['sentiment']:.2f}")
            print(f"5分钟成交量变化率: {row['volume_change_rate']:.2f}%")

def main():
    analyzer = HuaweiAscendAnalyzer()
    analyzer.analyze_stocks()

if __name__ == "__main__":
    main()
