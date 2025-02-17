import os
import sys
import json
from typing import Dict, Union, List

# 获取 workflow 目录（脚本实际位置的上级目录）
workflow_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将 workflow 目录添加到 Python 路径
sys.path.append(workflow_dir)

from stock_utils import StockUtils
from fund_utils import sFundUtils

def format_security_info(result: Dict[str, Union[str, float]], is_fund: bool = False) -> Dict:
    """格式化证券信息为 workflow 格式"""
    # 股票价格不需要乘以100，只有涨跌幅需要
    price = result['price'] if is_fund else result['price'] * 1000
    change = result['change_percent'] if is_fund else result['change_percent'] * 100

    # 构建标题（名称、代码、价格和涨跌）
    title = f"{result['name']}({result['code']}) 价格:{price:>8.3f} 涨幅:{change:>+6.2f}%"

    # 构建副标题（其他指标）
    subtitle_parts = []
    if is_fund:
        subtitle_parts.extend([
            f"溢价: {result['premium_rate']:>+6.2f}%",
            f"估值: {result['nav']:>8.4f}",
            f"换手: {result['turnover_rate']:>6.2f}%"
        ])
    else:
        # 股票数据处理，使用与 stock_query.py 相同的字段
        if 'turnover_rate' in result:
            turnover = result['turnover_rate'] * 100
            subtitle_parts.append(f"换手: {turnover:>6.2f}%")
        if 'market_value' in result:
            market_value = result['market_value'] / 100  # 转换为亿
            subtitle_parts.append(f"市值: {market_value:>8.2f}亿")
        if 'pe_ratio' in result:
            pe = result['pe_ratio'] * 100
            subtitle_parts.append(f"市盈: {pe:>6.2f}")

    return {
        "title": title,
        "subtitle": " | ".join(subtitle_parts),
        "arg": result['code'],
        "valid": True
    }

def query_securities(codes: List[str]) -> None:
    """查询证券信息并以 workflow 格式输出"""
    fund_utils = FundUtils()
    stock_utils = StockUtils()

    items = []

    # 处理所有代码
    for code in codes:
        try:
            if code.startswith(('16', '50', '51', '52', '56', '58')):
                result = fund_utils.get_fund_info(code)
                if 'error' not in result:
                    items.append(format_security_info(result, is_fund=True))
            else:
                result = stock_utils.get_stock_info(code)
                if 'error' not in result:
                    items.append(format_security_info(result))
        except Exception as e:
            items.append({
                "title": f"错误: {code}",
                "subtitle": str(e),
                "valid": False
            })

    # 输出 workflow 格式的 JSON
    print(json.dumps({"items": items}, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "items": [{
                "title": "请输入证券代码",
                "subtitle": "示例: 501311 600519 159949",
                "valid": False
            }]
        }))
        return

    # 将输入的字符串按空格分割成多个代码
    codes = sys.argv[1].split()
    # codes = ['501311','600519','159949']
    query_securities(codes)

if __name__ == "__main__":
    main()
