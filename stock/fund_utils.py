import requests
import json
import time
from typing import Dict, Union

class FundUtils:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_fund_nav(self, fund_code: str) -> float:
        """获取基金净值，优先获取实时估值"""
        try:
            # 1. 首先尝试从天天基金获取实时估值（这个API对海外ETF更准确）
            url = f'http://fundgz.1234567.com.cn/js/{fund_code}.js'
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200 and len(response.text) > 8:
                try:
                    nav_data = json.loads(response.text[8:-2])
                    est_nav = float(nav_data.get('gsz', 0))
                    if est_nav > 0:
                        print(f"获取到天天基金实时估值: {est_nav}")
                        return est_nav
                except:
                    pass

            # 2. 如果上面失败，尝试从东方财富API获取实时估值
            url2 = 'http://push2.eastmoney.com/api/qt/stock/get'

            # 处理基金代码格式
            if fund_code.startswith(('50', '51', '52', '53', '56', '58')):
                market = '1'  # 上证基金
            else:
                market = '0'  # 深证基金

            params = {
                'secid': f'{market}.{fund_code}',
                'fields': 'f43,f58,f71,f169,f170,f171,f126,f168,f170,f161',  # f71是实时估值
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fltt': '2',
                'cb': f'jQuery.jQuery{int(time.time() * 1000)}'
            }

            response2 = requests.get(url2, params=params, headers=self.headers)
            if response2.status_code == 200:
                data_text = response2.text
                json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
                data = json.loads(json_str)
                if 'data' in data and data['data']:
                    est_nav = float(data['data'].get('f71', 0))
                    if est_nav > 0:
                        est_nav = est_nav   # 转换为元
                        print(f"获取到东方财富实时估值: {est_nav}")
                        return est_nav

            # 3. 尝试从基金页面获取估值
            url3 = f'http://fund.eastmoney.com/{fund_code}.html'
            response3 = requests.get(url3, headers=self.headers)
            response3.encoding = 'utf-8'

            if response3.status_code == 200:
                text = response3.text
                # 先尝试获取估值
                est_index = text.find('"gz_gsz":"')
                if est_index > -1:
                    est_text = text[est_index:est_index+100]
                    est_parts = est_text.split('"')
                    for i, part in enumerate(est_parts):
                        if part == 'gz_gsz':
                            est_nav = float(est_parts[i+2])
                            print(f"从页面获取到实时估值: {est_nav}")
                            return est_nav

            # 4. 最后尝试获取历史净值
            url4 = f'http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&page=1&per=1'
            response4 = requests.get(url4, headers=self.headers)
            response4.encoding = 'utf-8'

            if response4.status_code == 200:
                text = response4.text
                if 'value' in text:
                    nav = float(text.split('value')[1].split('"')[1])
                    print(f"获取到历史净值: {nav}")
                    return nav

            print(f"未能获取到基金 {fund_code} 的净值或估值")
            return 0

        except Exception as e:
            print(f"获取净值失败: {str(e)}")
            return 0

    def get_fund_info(self, fund_code: str) -> Dict[str, Union[str, float]]:
        """获取基金基本信息"""
        try:
            # 使用东方财富的行情API
            url = 'http://push2.eastmoney.com/api/qt/stock/get'

            # 处理基金代码格式
            if fund_code.startswith(('50', '51', '52', '53', '56', '58')):
                market = '1'  # 上证基金
            else:
                market = '0'  # 深证基金

            params = {
                'secid': f'{market}.{fund_code}',
                'fields': 'f43,f58,f8,f51,f169,f170,f171,f116,f71,f161',  # f169是涨跌，f170是涨跌幅
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fltt': '2',
                'cb': f'jQuery.jQuery{int(time.time() * 1000)}'
            }

            response = requests.get(url, params=params, headers=self.headers)
            data_text = response.text

            try:
                json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
                data = json.loads(json_str)
            except Exception as e:
                return {'error': f'解析JSON失败: {str(e)}'}

            if 'data' not in data or not data['data']:
                return {'error': '数据为空'}

            stock_data = data['data']

            # 打印原始数据
            # print("\n原始数据:")
            # print(f"价格(f43): {stock_data.get('f43')}")
            # print(f"名称(f58): {stock_data.get('f58')}")
            # print(f"换手率1(f8): {stock_data.get('f8')}")
            # print(f"换手率2(f51): {stock_data.get('f51')}")
            # print(f"涨跌幅(f170): {stock_data.get('f170')}")
            # print(f"总市值(f116): {stock_data.get('f116')}")
            # print(f"估值(f71): {stock_data.get('f71')}")
            # print(f"溢价率(f161): {stock_data.get('f161')}")
            # print(f"净值1(f111): {stock_data.get('f111')}")
            # print(f"净值2(f191): {stock_data.get('f191')}")
            # print(f"净值3(f192): {stock_data.get('f192')}")

            def safe_float(value, default=0):
                if not value or value == '':
                    return default
                try:
                    return float(value)
                except:
                    return default

            # 获取基本信息
            price = safe_float(stock_data.get('f43'))
            if price == 0:
                return {'error': '基金价格为0或未获取到'}

            fund_name = stock_data.get('f58', '')

            # 优先使用f170（涨跌幅），如果为空则使用f169（涨跌）计算
            change_percent = safe_float(stock_data.get('f170'))
            if change_percent == 0:
                change = safe_float(stock_data.get('f169'))
                if price > 0 and change != 0:
                    change_percent = (change / (price - change)) * 100

            turnover_rate = safe_float(stock_data.get('f8'))
            if turnover_rate == 0:
                turnover_rate = safe_float(stock_data.get('f51'))
            fund_amount = safe_float(stock_data.get('f116'))

            # 获取估值并计算溢价率
            est_nav = safe_float(stock_data.get('f71'))
            if est_nav > 0:
                est_nav = est_nav  # 转换为元
                premium_rate = round((price / est_nav - 1) * 100, 2)  # 修正溢价率计算公式
            else:
                est_nav = 0
                premium_rate = 0

            result = {
                'code': fund_code,
                'name': fund_name,
                'price': price,
                'change_percent': change_percent,
                'market_value': round(fund_amount / 100000000, 2),
                'premium_rate': premium_rate,
                'turnover_rate': turnover_rate,
                'nav': est_nav
            }

            # print("\n处理结果:")
            # print(json.dumps(result, indent=2, ensure_ascii=False))

            return result

        except Exception as e:
            print(f"处理基金 {fund_code} 时出错: {str(e)}")
            return {'error': f'获取数据失败: {str(e)}'}

    def check_purchase_status(self, fund_code: str) -> Dict[str, Union[bool, str, float]]:
        """检查基金是否可以申购及申购限额"""
        try:
            # 获取基金申购状态
            url = f"http://fundgz.1234567.com.cn/js/{fund_code}.js"
            response = requests.get(url, headers=self.headers)

            # 通过天天基金获取申购状态
            url2 = f"http://fund.eastmoney.com/{fund_code}.html"
            response2 = requests.get(url2, headers=self.headers)

            # 如果基金已经终止或者暂停申购，页面会有相关提示
            if "暂停申购" in response2.text or "终止" in response2.text:
                return {
                    'can_purchase': False,
                    'message': '基金暂停申购或已终止',
                    'limit': 0
                }

            # 获取申购限额（实际应用中需要根据具体基金的页面结构解析）
            # 这里简单处理，假设都可以申购，限额设为一个较大值
            return {
                'can_purchase': True,
                'message': '可以申购',
                'limit': 1000000  # 默认限额100万
            }

        except Exception as e:
            return {
                'can_purchase': False,
                'message': f'检查申购状态失败: {str(e)}',
                'limit': 0
            }

    def get_fund_list(self) -> list:
        """获取场内基金列表"""
        funds = []
        try:
            # 使用东方财富行情中心的API
            url = "http://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': 1,
                'pz': 2000,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'b:MK0021,b:MK0022',  # MK0021是LOF基金，MK0022是ETF基金
                'fields': 'f12,f14',  # f12:代码, f14:名称
                'cb': f'jQuery.jQuery{int(time.time() * 1000)}'
            }

            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                data_text = response.text
                json_str = data_text[data_text.index('(') + 1:data_text.rindex(')')]
                data = json.loads(json_str)

                if 'data' in data and 'diff' in data['data']:
                    for item in data['data']['diff']:
                        code = item.get('f12', '')
                        name = item.get('f14', '')
                        print(f"检查: {code} - {name}")
                        # 只保留LOF基金
                        if code and (code.startswith('16') or code.startswith('501')):
                            funds.append(code)

            print(f"总共获取到 {len(funds)} 只LOF基金")

        except Exception as e:
            print(f"获取基金列表失败: {str(e)}")
            if 'data_text' in locals():
                print(f"错误详情: {data_text}")

        return funds
