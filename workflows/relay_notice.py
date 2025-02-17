import sys
import time
import os
from datetime import datetime, timedelta

def parse_input(input_text):
    """
    解析用户输入，返回提醒内容和延迟的秒数。
    :param input_text: 用户输入内容，例如 "去开会 5min"
    :return: (message, delay_in_seconds)
    """
    try:
        if not input_text:
            raise ValueError("输入为空，请输入提醒内容和时间，例如: 去开会 5min")

        # 将输入按空格拆分，假设格式为 "提醒内容 时长"
        parts = input_text.rsplit(" ", 1)  # 从右拆分一次，获取时间
        if len(parts) != 2:
            raise ValueError("输入格式有误，请确保格式为: 提醒内容 时长")

        message = parts[0]  # 提醒的内容
        delay = parts[1]    # 时间部分，例如 5min

        # 解析时间（支持 min、h、s）
        if delay.endswith("min"):  # 分钟
            delay_in_seconds = int(delay[:-3]) * 60
        elif delay.endswith("h"):  # 小时
            delay_in_seconds = int(delay[:-1]) * 3600
        elif delay.endswith("s"):  # 秒
            delay_in_seconds = int(delay[:-1])
        else:
            raise ValueError("时间格式错误，仅支持 s(seconds), min(minutes), h(hours)")

        return message, delay_in_seconds
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

def set_reminder(message, delay_in_seconds):
    """
    设置提醒通知
    :param message: 提醒内容
    :param delay_in_seconds: 延迟时间（秒）
    """
    # 计算提醒时间
    reminder_time = datetime.now() + timedelta(seconds=delay_in_seconds)
    formatted_time = reminder_time.strftime("%Y-%m-%d %H:%M:%S")

    # 使用 `osascript` 调用 macOS 的通知
    script = f'''
    osascript -e 'display notification "{message}" with title "提醒"'
    '''

    # 执行延迟任务
    time.sleep(delay_in_seconds)

    # 弹窗提醒
    os.system(script)
def create_reminder(message, delay_seconds):
    # AppleScript 命令
    apple_script = f"""
    set reminderText to "{message}"
    set remindAfterSeconds to {delay_seconds}
    set remindTime to (current date) + remindAfterSeconds
    tell application "Reminders"
        tell list "自动提醒"
            make new reminder with properties {{name:reminderText, remind me date:remindTime}}
        end tell
    end tell
    """

    # 调用 osascript 执行 AppleScript
    os.system(f"osascript -e '{apple_script}'")

if __name__ == "__main__":
    # 接收输入内容
    input_text = " ".join(sys.argv[1:])
    # 示例：接收的输入是 "去开会 5min"
    message, delay_in_seconds = parse_input(input_text)  # 假设 parse_input 是之前定义的函数

    # 创建提醒事项
    create_reminder(message, delay_in_seconds)
