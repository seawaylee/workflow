import requests
import json
from typing import Dict, Union, Tuple
import time
import pandas as pd
from datetime import datetime, timedelta


class StockUtils:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def format_hk_code(self, code: str) -> str:
        """格式化港股代码为5位数字"""
        # 移除所有非数字字符
        code = ''.join(filter(str.isdigit, code))
        # 补0到5位
        return code.zfill(5)

    def get_stock_info(self, code: str) -> Dict[str, Union[str, float]]:
        """获取股票信息"""
        try:
            # 确定市场代码
            if code.startswith(('6', '688', '50', '51')):
                market = '1'  # 上证
                full_code = f'1.{code}'
            elif code.startswith(('0', '3', '2', '15', '16')):
                market = '0'  # 深证
                full_code = f'0.{code}'
            elif code.startswith(('1', '9')) or len(code) <= 4:  # 港股代码处理
                market = '116'  # 港股市场代码
                hk_code = self.format_hk_code(code)
                full_code = f'116.{hk_code}'
            else:
                return {'error': '无效的股票代码'}
            
            # 构建请求URL - 使用港股专用API
            if market == '116':
                url = 'http://push2his.eastmoney.com/api/qt/stock/get'
            else:
                url = 'http://push2.eastmoney.com/api/qt/stock/get'
            
            params = {
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'invt': 2,
                'fltt': 2,
                'fields': 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,f268,f250,f251,f252,f253,f254,f255,f256,f257,f258,f266,f269,f270,f271,f273,f274,f275,f127,f199,f128,f193,f196,f194,f195,f197,f80,f280,f281,f282,f284,f285,f286,f287,f292',
                'secid': full_code,
                'forcect': 1
            }
            
            if market == '116':
                params.update({
                    'fields': 'f43,f57,f58,f169,f170,f46,f44,f51,f168,f47,f164,f163,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,f268,f250,f251,f252,f253,f254,f255,f256,f257,f258,f266,f269,f270,f271,f273,f274,f275,f127,f199,f128,f193,f196,f194,f195,f197,f80,f280,f281,f282,f284,f285,f286,f287,f292,f295,f296,f297',
                    'iscca': '1'
                })
            
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if 'data' not in data:
                return {'error': '获取数据失败'}
            
            stock_data = data['data']
            
            # 解析数据
            result = {
                'code': code,
                'name': stock_data.get('f58', ''),  # 股票名称
                'price': float(stock_data.get('f43', 0)),  # 当前价格
                'pre_close': float(stock_data.get('f60', 0)),  # 昨收价
                'high': float(stock_data.get('f44', 0)),  # 最高
                'low': float(stock_data.get('f45', 0)),  # 最低
                'volume': float(stock_data.get('f47', 0)) / 10000,  # 成交量(手)
                'amount': float(stock_data.get('f48', 0)) / 10000,  # 成交额(万元)
                'turnover_rate': float(stock_data.get('f168', 0)),  # 换手率
                'market_value': float(stock_data.get('f116', 0)) / 100000000,  # 总市值(亿)
                'currency': 'HKD' if market == '116' else 'CNY'
            }
            
            return result
            
        except Exception:
            return {'error': '获取数据失败'}

    def get_fund_premium(self, fund_code: str) -> Dict[str, Union[str, float]]:
        """获取场内基金溢价率"""
        try:
            # 获取场内基金实时价格
            fund_info = self.get_stock_info(fund_code)
            if 'error' in fund_info:
                return fund_info

            # 获取基金净值
            url = f'http://fundgz.1234567.com.cn/js/{fund_code}.js'
            response = requests.get(url, headers=self.headers)

            # 解析JSONP格式数据
            data_text = response.text
            json_data = json.loads(data_text[8:-2])

            nav = float(json_data['dwjz'])  # 单位净值
            current_price = fund_info['price']  * 1000 # 已经是正确的元单位

            # 计算溢价率
            premium_rate = (current_price - nav) / nav * 100

            return {
                'code': fund_code,
                'name': fund_info['name'],  # 添加基金名称
                'price': current_price,
                'change_percent': fund_info['change_percent'] * 100,
                'nav': nav,
                'premium_rate': round(premium_rate, 2)
            }
        except Exception as e:
            return {'error': f'获取基金数据失败: {str(e)}'}

    def get_kline_data(self, code: str, days: int = 60) -> pd.DataFrame:
        """获取股票K线数据"""
        try:
            # 确定市场代码
            if code.startswith(('6', '688', '50', '51')):  # 上证股票、科创板、上证基金
                market = '1'  # 上证
                full_code = f'1.{code}'
            elif code.startswith(('0', '3', '2', '15', '16')):  # 深证股票、创业板、深证基金
                market = '0'  # 深证
                full_code = f'0.{code}'
            else:
                print(f"无法确定{code}的市场代码")
                return None

            # 计算起始时间
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 构建请求URL - 使用新的API
            url = 'http://83.push2his.eastmoney.com/api/qt/stock/kline/get'
            params = {
                'secid': full_code,
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K线
                'fqt': '1',    # 前复权
                'beg': start_date.strftime('%Y%m%d'),
                'end': end_date.strftime('%Y%m%d'),
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'rtntype': '6',
                'forcect': '1'
            }

            response = requests.get(url, params=params, headers=self.headers)
            
            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return None
            
            data = response.json()
            
            if 'data' not in data or not data['data'] or 'klines' not in data['data']:
                print(f"未获取到{code}的K线数据，API返回: {data}")
                return None

            # 解析K线数据
            klines = data['data']['klines']
            dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
            
            for kline in klines:
                date_str, o, h, l, c, v, *_ = kline.split(',')
                dates.append(pd.to_datetime(date_str))
                opens.append(float(o))
                highs.append(float(h))
                lows.append(float(l))
                closes.append(float(c))
                volumes.append(float(v))

            # 创建DataFrame
            df = pd.DataFrame({
                'Open': opens,
                'High': highs,
                'Low': lows,
                'Close': closes,
                'Volume': volumes
            }, index=dates)

            return df

        except Exception as e:
            print(f"获取K线数据失败: {str(e)}")
            print(f"请求URL: {url}")
            print(f"请求参数: {params}")
            return None

    def get_timeline_data(self, code: str) -> pd.DataFrame:
        """获取股票分时数据"""
        try:
            # 确定市场代码
            if code.startswith(('6', '688', '50', '51')):
                market = '1'
                full_code = f'1.{code}'
            elif code.startswith(('0', '3', '2', '15', '16')):
                market = '0'
                full_code = f'0.{code}'
            elif len(code) <= 5 and code.isdigit():  # 港股
                market = '116'
                code = self.format_hk_code(code)
                full_code = f'{market}.{code}'
            else:
                return pd.DataFrame()

            # 构建请求URL和参数
            if market == '116':
                url = 'http://push2his.eastmoney.com/api/qt/stock/trends2/get'
                params = {
                    'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11',
                    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                    'ndays': '1',
                    'iscr': '0',
                    'secid': full_code,
                    'forcect': '1',
                    'iscca': '1',
                    'lmt': '240'
                }
            else:
                url = 'http://push2.eastmoney.com/api/qt/stock/trends2/get'
                params = {
                    'fields1': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11',
                    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                    'ndays': '1',
                    'iscr': '0',
                    'secid': full_code,
                    'forcect': '1'
                }
            
            response = requests.get(url, params=params, headers=self.headers)
            data = response.json()
            
            if 'data' not in data or not data['data']:
                return pd.DataFrame()
            
            stock_data = data['data']
            pre_close = float(stock_data.get('preclose', 0))
            if pre_close == 0:
                pre_close = float(stock_data.get('f46', 0))
            
            trends = stock_data.get('trends', [])
            times, prices, amounts, volumes, avg_prices = [], [], [], [], []
            
            for trend in trends:
                try:
                    items = trend.split(',')
                    if len(items) < 7:
                        continue
                    
                    time_str = items[0]
                    price = float(items[1])
                    avg_price = float(items[2])
                    volume = float(items[5])
                    amount = float(items[6])
                    
                    try:
                        if '-' in time_str:
                            time = pd.to_datetime(time_str)
                        else:
                            time = pd.to_datetime(f"{datetime.now().strftime('%Y-%m-%d')} {time_str}")
                        
                        times.append(time)
                        prices.append(price)
                        amounts.append(amount)
                        volumes.append(volume)
                        avg_prices.append(avg_price)
                        
                    except ValueError:
                        continue
                    
                except Exception:
                    continue
            
            if not times:
                return pd.DataFrame()
            
            df = pd.DataFrame({
                'price': prices,
                'volume': volumes,
                'amount': amounts,
                'avg_price': avg_prices,
                'pre_close': pre_close
            }, index=times)
            
            df = df[~df.index.duplicated(keep='last')]
            df.sort_index(inplace=True)
            
            trading_mask = (
                ((df.index.hour == 9) & (df.index.minute >= 30)) |
                (df.index.hour == 10) |
                (df.index.hour == 11) |
                (df.index.hour == 13) |
                (df.index.hour == 14) |
                ((df.index.hour == 15) & (df.index.minute <= 59))
            )
            df = df[trading_mask]
            
            return df
            
        except Exception:
            return pd.DataFrame()
