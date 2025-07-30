#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Session 定时监测调度器 - 增强版
提供定时监测功能，支持间隔监测和crontab集成
支持自动撤销未授权session功能
"""

import time
import sys
import os
import subprocess
from datetime import datetime
import signal
import threading

# 确保输出立即刷新到文件
def flush_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()
    sys.stderr.flush()

class CursorSessionScheduler:
    def __init__(self, monitor_script_path=None):
        self.monitor_script_path = monitor_script_path or "cursor_session_monitor.py"
        self.running = False
        self.monitor_thread = None
        
    def run_monitor(self, threshold=2, strict_mode=False):
        """
        执行一次监测
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), self.monitor_script_path)
            if not os.path.exists(script_path):
                print(f"❌ 监测脚本不存在: {script_path}")
                return False
            
            cmd = [sys.executable, script_path]
            if strict_mode:
                cmd.append('--strict')
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行监测命令 (严格模式): {' '.join(cmd)}")
            else:
                cmd.append(str(threshold))
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 执行监测命令: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            print("监测结果:")
            print(result.stdout)
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"执行监测失败: {str(e)}")
            return False
    
    def start_interval_monitoring(self, interval_minutes=5, threshold=2, strict_mode=False):
        """
        开始间隔监测
        """
        if self.running:
            print("监测已在运行中...")
            return
        
        self.running = True
        if strict_mode:
            print(f"开始定时监测 (间隔: {interval_minutes}分钟, 🔒严格模式)")
        else:
            print(f"开始定时监测 (间隔: {interval_minutes}分钟, 阈值: {threshold})")
        print("📱 包含自动撤销未授权session功能")
        print("按 Ctrl+C 停止监测")
        
        def monitor_worker():
            while self.running:
                try:
                    self.run_monitor(threshold, strict_mode)
                    
                    # 等待指定间隔时间
                    for _ in range(interval_minutes * 60):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"监测过程中出错: {str(e)}")
                    time.sleep(10)  # 出错后等待10秒再继续
    
    def start_interval_monitoring_seconds(self, interval_seconds=60, threshold=2, strict_mode=False):
        """
        开始秒级间隔监测
        """
        if self.running:
            print("监测已在运行中...")
            return
        
        self.running = True
        if strict_mode:
            print(f"开始高频监测 (间隔: {interval_seconds}秒, 🔒严格模式)")
        else:
            print(f"开始高频监测 (间隔: {interval_seconds}秒, 阈值: {threshold})")
        print("📱 包含自动撤销未授权session功能")
        print("⚠️  高频监测会增加系统负载和API调用频率")
        print("按 Ctrl+C 停止监测")
        
        def monitor_worker():
            while self.running:
                try:
                    self.run_monitor(threshold, strict_mode)
                    
                    # 等待指定间隔时间（秒级）
                    for _ in range(interval_seconds):
                        if not self.running:
                            break
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"监测过程中出错: {str(e)}")
                    time.sleep(10)  # 出错后等待10秒再继续
        
        self.monitor_thread = threading.Thread(target=monitor_worker)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        try:
            self.monitor_thread.join()
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """
        停止监测
        """
        if self.running:
            self.running = False
            print("\n正在停止监测...")
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            print("监测已停止")
    
    def generate_crontab_entry(self, cron_expression, threshold=2, strict_mode=False):
        """
        生成crontab条目
        """
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), self.monitor_script_path))
        python_path = sys.executable
        
        # 构建命令参数
        if strict_mode:
            cmd_args = f"{python_path} {script_path} --strict"
            mode_desc = "严格模式"
        else:
            cmd_args = f"{python_path} {script_path} {threshold}"
            mode_desc = f"阈值: {threshold}"
        
        # 支持特殊的@reboot指令
        if cron_expression.lower() == "@reboot":
            crontab_entry = f"@reboot {cmd_args} >> /tmp/cursor_session_monitor.log 2>&1"
            print(f"建议的crontab条目 (开机自启动, {mode_desc}):")
            print("-" * 60)
            print(crontab_entry)
            print("-" * 60)
            print("\n⚠️  开机自启动说明:")
            print("• 系统启动后会立即执行一次监测")
            print("• 如需定时监测，请额外添加定时cron条目")
            print("• 建议同时配置定时监测确保持续保护")
            
            print("\n建议的完整配置:")
            print("@reboot " + f"{cmd_args} >> /tmp/cursor_session_monitor.log 2>&1")
            print("*/10 * * * * " + f"{cmd_args} >> /tmp/cursor_session_monitor.log 2>&1")
        else:
            crontab_entry = f"{cron_expression} {cmd_args} >> /tmp/cursor_session_monitor.log 2>&1"
            print(f"建议的crontab条目 (定时执行, {mode_desc}):")
            print("-" * 60)
            print(crontab_entry)
            print("-" * 60)
            print("\n📅 定时执行说明:")
            print("• 只在指定时间点执行，不会开机自启")
            print("• 系统重启后需等待下一个时间点才会执行")
            print("• 如需开机立即执行，请使用 '@reboot' 表达式")
            if strict_mode:
                print("• 🔒 严格模式：任何未授权session都将被立即撤销")
            else:
                print(f"• 普通模式：只有超过阈值{threshold}且存在未授权session时才撤销")
        
        print("\n使用方法:")
        print("1. 运行 'crontab -e' 编辑crontab")
        print("2. 添加上述条目")
        print("3. 保存并退出")
        print("4. 运行 'crontab -l' 验证配置")
        
        print("\n常见的cron表达式:")
        print("  每5分钟:   */5 * * * *")
        print("  每小时:    0 * * * *")
        print("  每天9点:   0 9 * * *")
        print("  工作日9-18点每小时: 0 9-18 * * 1-5")
        print("  开机自启:  @reboot")
        print("\n⚠️  注意: 自动撤销功能将删除非授权session，请确认白名单配置正确！")
        if strict_mode:
            print("🔒 严格模式推荐用于生产环境，提供最高安全性！")
        
        return crontab_entry

def print_usage():
    """
    打印使用说明
    """
    print("""
Cursor Session 定时监测调度器 - 增强版

🔒 新功能: 自动撤销未授权session + 严格模式

使用方法:
  python3 cursor_session_scheduler.py [命令] [参数] [--strict]

命令:
  run [阈值|--strict]            - 执行一次监测 (默认阈值: 2)
  interval [间隔分钟] [阈值] [--strict] - 开始间隔监测 (默认: 5分钟, 阈值: 2)  
  seconds [间隔秒数] [阈值] [--strict]  - 开始秒级监测 (默认: 60秒, 阈值: 2)
  crontab [cron表达式] [阈值]    - 生成crontab条目

模式说明:
  普通模式: 只有当session数量 > 阈值 且存在未授权session时才撤销
  严格模式: 忽略阈值，只要发现未授权session就立即撤销 (推荐生产环境)

示例:
  # 普通模式
  python3 cursor_session_scheduler.py run                    # 执行一次监测，阈值2
  python3 cursor_session_scheduler.py run 3                  # 阈值设为3执行一次监测
  python3 cursor_session_scheduler.py interval 10 3          # 每10分钟监测一次，阈值为3
  
  # 严格模式 (推荐)
  python3 cursor_session_scheduler.py run --strict           # 严格模式，立即清理未授权session
  python3 cursor_session_scheduler.py interval 5 --strict    # 每5分钟严格模式监测
  python3 cursor_session_scheduler.py seconds 30 --strict    # 每30秒严格模式监测

⚠️  重要提醒:
- 监测脚本包含自动撤销功能，会删除非白名单session
- 请确认白名单session配置正确后再使用
- 🔒 严格模式推荐用于生产环境，提供最高安全性
- 普通模式适合测试阶段，可设置高阈值观察行为
- 秒级监测会增加系统负载，建议间隔不要太短（建议≥30秒）
""")

def main():
    scheduler = CursorSessionScheduler()
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    # 检查是否有strict模式参数
    strict_mode = '--strict' in sys.argv or '-s' in sys.argv or 'strict' in [arg.lower() for arg in sys.argv]
    args = [arg for arg in sys.argv if arg.lower() not in ['--strict', '-s', 'strict']]
    
    command = args[1].lower()
    
    if command == "run":
        # 执行一次监测
        if strict_mode:
            print("🔒 使用严格模式执行监测")
            success = scheduler.run_monitor(strict_mode=True)
        else:
            threshold = int(args[2]) if len(args) > 2 else 2
            success = scheduler.run_monitor(threshold, strict_mode=False)
        sys.exit(0 if success else 1)
        
    elif command == "interval":
        # 间隔监测（分钟级）
        interval_minutes = int(args[2]) if len(args) > 2 else 5
        threshold = int(args[3]) if len(args) > 3 and not strict_mode else 2
        
        # 设置信号处理器
        def signal_handler(signum, frame):
            scheduler.stop_monitoring()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if strict_mode:
            print("🔒 使用严格模式进行间隔监测")
        scheduler.start_interval_monitoring(interval_minutes, threshold, strict_mode)
        
    elif command == "seconds":
        # 间隔监测（秒级）
        interval_seconds = int(args[2]) if len(args) > 2 else 60
        threshold = int(args[3]) if len(args) > 3 and not strict_mode else 2
        
        # 安全检查：防止间隔太短
        if interval_seconds < 5:
            print("⚠️  警告: 间隔时间过短可能导致系统负载过高和API限流")
            print("建议最小间隔为5秒，你确定要继续吗？(y/N)")
            confirm = input().lower()
            if confirm != 'y':
                print("已取消执行")
                return
        
        # 设置信号处理器
        def signal_handler(signum, frame):
            scheduler.stop_monitoring()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if strict_mode:
            print("🔒 使用严格模式进行秒级监测")
        scheduler.start_interval_monitoring_seconds(interval_seconds, threshold, strict_mode)
        
    elif command == "crontab":
        # 生成crontab条目
        if len(args) < 3:
            print("错误: 请提供cron表达式")
            print("示例: python3 cursor_session_scheduler.py crontab \"*/5 * * * *\"")
            return
        
        cron_expression = args[2]
        threshold = int(args[3]) if len(args) > 3 else 2
        scheduler.generate_crontab_entry(cron_expression, threshold, strict_mode)
        
    else:
        print(f"未知命令: {command}")
        print_usage()

if __name__ == "__main__":
    main()