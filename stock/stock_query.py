from stock_utils import StockUtils
from fund_utils import FundUtils
import sys
from typing import Dict, Union, List, Any
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import base64
import json
import numpy as np

def is_fund_code(code: str) -> bool:
    """判断是否为基金代码"""
    # LOF基金: 16xxxx, 501xxx
    # ETF基金: 51xxxx, 52xxxx, 56xxxx, 58xxxx
    # 货币ETF: 511xxx
    # 债券ETF: 511xxx, 512xxx
    # 股票ETF: 510xxx, 512xxx, 513xxx, 515xxx, 516xxx, 588xxx
    fund_prefixes = ('16', '50', '51', '52', '56', '58')
    return code.startswith(fund_prefixes)

def format_fund_info(result: Dict[str, Union[str, float]]) -> str:
    """格式化基金信息输出"""
    return (
        f"{result['name']} ({result['code']}) "
        f"价格: {result['price']:.3f} "
        f"涨跌: {result['change_percent']:+.2f}% "
        f"溢价: {result['premium_rate']:+.2f}% "
        f"估值: {result['nav']:.4f} "
        f"换手: {result['turnover_rate']:.2f}%"
    )

def format_stock_info(result: Dict[str, Union[str, float]]) -> str:
    """格式化股票信息输出"""
    info = f"{result['name']} ({result['code']}) "
    
    # 添加货币标识
    currency = result.get('currency', 'CNY')
    price = result['price']
    info += f"价格: {price:.3f} {currency} "
    
    # 添加涨跌幅
    change = result['change_percent']
    info += f"涨跌: {change:+.2f}% "
    
    # 添加成交信息（如果有）
    if 'volume' in result:
        volume = result['volume'] / 10000  # 转换为万股
        amount = result['amount']  # 已经是万元
        info += f"成交量: {volume:.2f}万股 成交额: {amount:.2f}万{currency} "
    
    # 添加最高最低价（如果有）
    if 'high' in result:
        info += f"最高: {result['high']:.3f} 最低: {result['low']:.3f} "
    
    # 添加其他指标
    if 'turnover_rate' in result:
        info += f"换手: {result['turnover_rate']:.2f}% "
    if 'market_value' in result:
        info += f"市值: {result['market_value']:.2f}亿{currency} "
    if 'pe_ratio' in result and result['pe_ratio'] != '-':
        info += f"市盈: {float(result['pe_ratio']):.2f}"
        
    return info

def plot_kline(code: str, data: pd.DataFrame, stock_info: Dict[str, Any]) -> None:
    """绘制K线图并保存"""
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['PingFang HK', 'Microsoft YaHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图表
    fig = plt.figure(figsize=(15, 8))
    
    # 上方K线图，占5/6
    ax1 = plt.subplot2grid((6, 1), (0, 0), rowspan=5)
    
    # 使用传入的股票信息计算涨跌幅
    current_price = stock_info['price']
    pre_close = stock_info['pre_close']
    change = (current_price - pre_close) / pre_close * 100 if pre_close != 0 else 0.0
    
    # 计算实际的最大涨跌幅
    actual_max_change = ((data['price'].max() - pre_close) / pre_close * 100)
    actual_min_change = ((data['price'].min() - pre_close) / pre_close * 100)
    
    # 使用最大的绝对值来确定范围，保证对称
    max_abs_change = max(abs(actual_max_change), abs(actual_min_change))
    
    # 动态确定步长
    if max_abs_change < 1:
        step = 0.2  # 0.2%的步长
    elif max_abs_change < 2:
        step = 0.5  # 0.5%的步长
    elif max_abs_change < 5:
        step = 1.0  # 1%的步长
    else:
        step = 2.0  # 2%的步长
    
    # 计算主要刻度（整数刻度）
    main_ticks = np.arange(0, max_abs_change, step)
    # 移除最后一个整数刻度如果它太接近最大值
    if max_abs_change - main_ticks[-1] < step * 0.3:
        main_ticks = main_ticks[:-1]
    
    # 添加最大值刻度（精确到小数点后一位）
    max_tick = np.ceil(max_abs_change * 10) / 10  # 向上取整到0.1%
    min_tick = -max_tick
    
    # 生成完整的刻度列表
    positive_ticks = np.append(main_ticks, max_tick)
    negative_ticks = -positive_ticks[::-1]
    ticks = np.concatenate([negative_ticks, [0], positive_ticks])
    
    # 添加小边距避免线条碰到边框
    margin = step * 0.1  # 步长的10%作为边距
    
    # 设置涨跌幅轴的范围和刻度
    ax2 = ax1.twinx()
    ax2.set_ylim(min_tick - margin, max_tick + margin)
    ax2.set_yticks(ticks)
    ax2.set_ylabel('涨跌幅(%)')
    
    # 设置涨跌幅刻度的颜色和标签
    for tick in ticks:
        if abs(tick) < 0.01:  # 处理接近0的情况
            ax2.text(1.02, tick, '0.00%', transform=ax2.get_yaxis_transform(),
                    color='gray', va='center')
        elif tick > 0:
            # 最大值显示一位小数，其他为整数
            if tick == max_tick:
                ax2.text(1.02, tick, f'{tick:+.1f}%', transform=ax2.get_yaxis_transform(),
                        color='red', va='center')
            else:
                ax2.text(1.02, tick, f'{tick:+.0f}%', transform=ax2.get_yaxis_transform(),
                        color='red', va='center')
        else:
            # 最小值显示一位小数，其他为整数
            if tick == min_tick:
                ax2.text(1.02, tick, f'{tick:.1f}%', transform=ax2.get_yaxis_transform(),
                        color='green', va='center')
            else:
                ax2.text(1.02, tick, f'{tick:.0f}%', transform=ax2.get_yaxis_transform(),
                        color='green', va='center')
    
    # 隐藏右侧Y轴的刻度线和标签
    ax2.set_yticklabels([])
    
    # 绘制价格线（根据涨跌设置颜色，并添加轻微透明度）
    price_color = ['red' if p >= pre_close else 'green' for p in data['price']]
    for i in range(1, len(data['price'])):
        ax1.plot(data.index[i-1:i+1], data['price'].iloc[i-1:i+1], 
                 color=price_color[i], linewidth=1.2, alpha=0.9)
    
    # 添加昨收价参考线（使用更细的虚线）
    ax1.axhline(y=pre_close, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
    
    # 设置标题
    ax1.set_title(f"{stock_info['name']} ({code}) 分时图 - {datetime.now().strftime('%Y-%m-%d')} 涨跌幅: {change:.2f}%")
    
    # 设置左侧Y轴（价格）
    ax1.set_ylabel('价格(元)')
    
    # 设置网格
    ax1.grid(True, linestyle='--', alpha=0.3)
    ax1.set_facecolor('#F6F6F6')
    
    # 下方成交量图，占1/6
    ax3 = plt.subplot2grid((6, 1), (5, 0))
    
    # 将成交额转换为千万元单位
    amount_in_10m = data['amount'] / 1000
    
    # 绘制成交额柱状图（东方财富风格）
    for i in range(len(amount_in_10m)):
        if i > 0:
            color = 'red' if data['price'].iloc[i] > data['price'].iloc[i-1] else 'green'
        else:
            color = 'red' if data['price'].iloc[i] > pre_close else 'green'
        ax3.bar(data.index[i], amount_in_10m.iloc[i], color=color, alpha=0.7, width=0.0003)
    
    # 设置成交量图样式
    ax3.grid(True, linestyle='--', alpha=0.3)
    ax3.set_ylabel('成交额(千万元)')
    ax3.set_facecolor('#F6F6F6')
    
    # 设置x轴时间范围和格式
    today = pd.Timestamp.now().date()
    xlim_min = pd.Timestamp.combine(today, pd.Timestamp('09:30:00').time())
    xlim_max = pd.Timestamp.combine(today, pd.Timestamp('15:00:00').time())
    
    ax1.set_xlim(xlim_min, xlim_max)
    ax3.set_xlim(xlim_min, xlim_max)
    
    # 设置x轴时间格式
    time_formatter = mdates.DateFormatter('%H:%M')
    ax1.xaxis.set_major_formatter(time_formatter)
    ax3.xaxis.set_major_formatter(time_formatter)
    
    # 创建固定的时间刻度
    trading_hours = [
        pd.Timestamp.combine(today, pd.Timestamp(f'{h:02d}:{m:02d}:00').time())
        for h in [9, 10, 11, 13, 14, 15]
        for m in [0, 30] if not (h == 9 and m == 0) and not (h == 15 and m == 30)
    ]
    trading_hours.insert(0, xlim_min)  # 添加9:30
    
    # 设置刻度
    ax1.set_xticks(trading_hours)
    ax3.set_xticks(trading_hours)
    
    # 添加中午休市时段的灰色背景
    lunch_start = pd.Timestamp.combine(today, pd.Timestamp('11:30:00').time())
    lunch_end = pd.Timestamp.combine(today, pd.Timestamp('13:00:00').time())
    
    ax1.axvspan(lunch_start, lunch_end, color='gray', alpha=0.1)
    ax3.axvspan(lunch_start, lunch_end, color='gray', alpha=0.1)
    
    # 自动调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('kline.png', dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()

def plot_timeline(code: str, data: pd.DataFrame, save_dir: str = 'charts') -> str:
    """绘制分时图"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # 检查数据是否为空
    if data.empty:
        return None
    
    try:
        # 设置严格的时间范围
        morning_start = pd.Timestamp(data.index[0].date()).replace(hour=9, minute=30)
        morning_end = pd.Timestamp(data.index[0].date()).replace(hour=12, minute=0)  # 修改为12:00
        afternoon_start = pd.Timestamp(data.index[0].date()).replace(hour=13, minute=0)
        afternoon_end = pd.Timestamp(data.index[0].date()).replace(hour=16, minute=0)  # 修改为16:00
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac系统使用
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[3, 1])
        
        # 分割上午和下午的数据
        morning_mask = data.index.hour < 12
        afternoon_mask = data.index.hour >= 12
        
        # 绘制价格走势（分段绘制）
        ax1.plot(data[morning_mask].index, data[morning_mask]['price'], 'b-', linewidth=1.5)
        ax1.plot(data[afternoon_mask].index, data[afternoon_mask]['price'], 'b-', linewidth=1.5)
        
        # 添加均价线（分段绘制）
        if 'avg_price' in data.columns:
            ax1.plot(data[morning_mask].index, data[morning_mask]['avg_price'], 'r--', linewidth=1, alpha=0.8)
            ax1.plot(data[afternoon_mask].index, data[afternoon_mask]['avg_price'], 'r--', linewidth=1, alpha=0.8)
            ax1.legend(['价格', '均价'], loc='upper left')
        
        # 设置价格图样式
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1.set_title(f'{code} 分时图 - {datetime.now().strftime("%Y-%m-%d")}', fontsize=12, pad=15)
        ax1.set_ylabel('价格(元)', fontsize=10)
        
        # 计算涨跌幅基准线和涨跌幅
        if 'pre_close' in data.columns and len(data) > 0:
            base_price = data['pre_close'].iloc[0]
            current_price = data['price'].iloc[-1]
            change_percent = (current_price - base_price) / base_price * 100
            
            # 添加基准线
            ax1.axhline(y=base_price, color='gray', linestyle='-', alpha=0.3)
            
            # 添加涨跌幅标注
            title = ax1.get_title()
            ax1.set_title(f'{title} 涨跌幅：{change_percent:+.2f}%')
            
            # 计算合理的价格范围
            price_max = data['price'].max()
            price_min = data['price'].min()
            price_range = price_max - price_min
            
            # 设置适当的边距，确保价格在合理范围内
            margin_ratio = 0.1  # 上下留出10%的边距
            y_margin = price_range * margin_ratio
            y_min = max(0, price_min - y_margin)  # 确保不会出现负数
            y_max = price_max + y_margin
            
            ax1.set_ylim(y_min, y_max)
            
            # 设置价格轴的刻度间隔
            from matplotlib.ticker import AutoMinorLocator, MaxNLocator
            ax1.yaxis.set_major_locator(MaxNLocator(nbins=10))  # 设置主刻度数量
            ax1.yaxis.set_minor_locator(AutoMinorLocator())  # 添加次要刻度
            ax1.grid(True, which='both', linestyle='--', alpha=0.3)
        
        # 绘制成交量（分段绘制）
        if 'volume' in data.columns and len(data) > 0:
            # 计算每个时间点相对于前一个时间点的价格变化
            price_change = data['price'].diff()
            
            # 分别获取上涨和下跌的数据点
            rise_mask = price_change >= 0
            fall_mask = price_change < 0
            
            bar_width = 0.001  # 减小柱状图宽度
            
            # 上午数据
            morning_data = data[morning_mask]
            morning_rise = morning_data[rise_mask[morning_mask]]
            morning_fall = morning_data[fall_mask[morning_mask]]
            
            # 下午数据
            afternoon_data = data[afternoon_mask]
            afternoon_rise = afternoon_data[rise_mask[afternoon_mask]]
            afternoon_fall = afternoon_data[fall_mask[afternoon_mask]]
            
            # 绘制上涨柱状图（红色）
            ax2.bar(morning_rise.index, morning_rise['volume'], 
                    width=bar_width, color='red', alpha=0.7, label='上涨')
            ax2.bar(afternoon_rise.index, afternoon_rise['volume'], 
                    width=bar_width, color='red', alpha=0.7)
            
            # 绘制下跌柱状图（绿色）
            ax2.bar(morning_fall.index, morning_fall['volume'], 
                    width=bar_width, color='green', alpha=0.7, label='下跌')
            ax2.bar(afternoon_fall.index, afternoon_fall['volume'], 
                    width=bar_width, color='green', alpha=0.7)
            
            ax2.set_ylabel('成交量', fontsize=10)
            ax2.grid(True, linestyle='--', alpha=0.3)
            
            # 添加图例
            ax2.legend(loc='upper right')
            
            # 设置成交量图的y轴刻度（以手/万手为单位）
            def format_volume(x, p):
                if x >= 1000000:  # 100万手
                    return f'{x/10000:.0f}万手'
                else:
                    return f'{x/100:.0f}手'
            ax2.yaxis.set_major_formatter(plt.FuncFormatter(format_volume))
        
        # 设置x轴范围和格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            plt.setp(ax.get_xticklabels(), rotation=45)
            
            # 添加午休时段的灰色背景
            ax.axvspan(morning_end, afternoon_start, color='lightgray', alpha=0.3)
        
        # 自动调整布局
        plt.tight_layout()
        
        # 保存图表
        filename = f"{code}_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(save_dir, filename)
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return filepath
        
    except Exception as e:
        return None

def encode_image_base64(image_path: str) -> str:
    """将图片转换为Base64编码"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_securities(codes: List[str]):
    """查询证券信息"""
    # 检查输入的代码长度
    if not codes or len(codes[0]) < 4:  # 股票代码至少4位
        return print(json.dumps({
            "items": [{
                "title": "请输入完整的股票代码",
                "subtitle": "至少需要4位数字",
                "valid": False
            }]
        }))
    
    stock_utils = StockUtils()
    fund_utils = FundUtils()
    
    results = []
    for code in codes:
        # 检查代码格式
        if not code.isdigit():
            continue
            
        # 尝试获取股票信息
        stock_info = stock_utils.get_stock_info(code)
        if stock_info and not stock_info.get('error'):
            # 获取分时数据
            df = stock_utils.get_timeline_data(code)
            if not df.empty:
                df['name'] = stock_info['name']
                plot_kline(code, df, stock_info)
                
            # 构建标题（包含价格和涨跌幅）
            current_price = stock_info.get('price', 0)
            change_percent = (current_price - stock_info.get('pre_close', 0)) / stock_info.get('pre_close', 1) * 100
            title = f"{stock_info['name']} ({code}) {current_price:.3f} {stock_info.get('currency', 'CNY')} {change_percent:+.2f}%"
            
            # 构建副标题信息
            subtitle_parts = []
            
            # 添加可选信息
            if 'volume' in stock_info:
                subtitle_parts.append(f"成交量: {stock_info['volume']:.2f}万股")
            if 'amount' in stock_info:
                subtitle_parts.append(f"成交额: {stock_info['amount']:.2f}万{stock_info.get('currency', 'CNY')}")
            if 'high' in stock_info:
                subtitle_parts.append(f"最高: {stock_info['high']:.3f}")
            if 'low' in stock_info:
                subtitle_parts.append(f"最低: {stock_info['low']:.3f}")
            if 'turnover_rate' in stock_info:
                subtitle_parts.append(f"换手: {stock_info['turnover_rate']:.2f}%")
            if 'market_value' in stock_info:
                subtitle_parts.append(f"市值: {stock_info['market_value']:.2f}亿{stock_info.get('currency', 'CNY')}")
                
            # 获取图片的绝对路径和目录
            kline_path = os.path.abspath('kline.png')
            kline_dir = os.path.dirname(kline_path)
            
            # 构建第一个结果项（股票信息）
            results.append({
                "title": title,
                "subtitle": " ".join(subtitle_parts),
                "type": "股票",
                "valid": True,
                "arg": code,
                "icon": {
                    "type": "default"  # 使用默认图标，不显示预览
                }
            })
            
            # 构建第二个结果项（打开图片）
            results.append({
                "title": f"{stock_info['name']} ({code}) K线图",
                "subtitle": "按 Enter 打开图片",
                "valid": True,
                "arg": kline_path,
                "type": "图表",
                "icon": {
                    "type": "default"  # 使用默认图标，不显示预览
                }
            })
            continue

        # 尝试获取基金信息
        fund_info = fund_utils.get_fund_info(code)
        if fund_info and not fund_info.get('error'):
            # 构建标题（包含价格和涨跌幅）
            title = f"{fund_info['name']} ({code}) {fund_info['price']:.3f} {fund_info['change']:+.2f}%"
            
            # 构建副标题
            subtitle = f"溢价: {fund_info['premium']:+.2f}% 估值: {fund_info['estimate']:.4f} 换手: {fund_info['turnover']:.2f}%"
            
            result = {
                "title": title,
                "subtitle": subtitle,
                "type": "基金",
                "valid": True,
                "arg": code
            }
            results.append(result)
            continue

    # 只输出 Alfred 需要的 JSON 格式
    if results:
        print(json.dumps({"items": results}, ensure_ascii=False))

def open_file(filepath: str) -> None:
    """跨平台打开文件"""
    import platform
    system = platform.system()
    
    try:
        if system == 'Darwin':       # macOS
            os.system(f'open "{filepath}"')
        elif system == 'Windows':    # Windows
            os.system(f'start "" "{filepath}"')
        elif system == 'Linux':      # Linux
            os.system(f'xdg-open "{filepath}"')
    except Exception as e:
            print(f"打开文件失败: {e}")

def main():
    if len(sys.argv) < 2:
        print("使用方法: python stock_query.py <代码1> [代码2] [代码3] ...")
        print("示例: python stock_query.py 501311 600519 159949")
        return
    
    query_securities(sys.argv[1:])

if __name__ == "__main__":
    main()
