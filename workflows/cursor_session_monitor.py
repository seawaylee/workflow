#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor Session 监测脚本 - 增强版
监测cursor活跃session数量，当超过阈值时发送报警通知
并自动撤销非授权的session
"""

import requests
import json
import os
import sys
from datetime import datetime

class CursorSessionMonitor:
    def __init__(self):
        # Cursor API端点
        self.api_url = "https://cursor.com/api/auth/sessions"
        self.revoke_url = "https://cursor.com/api/auth/sessions/revoke"

        # 用户提供的cookies
        self.cookies = {
            'WorkosCursorSessionToken': 'user_01JXWVM0FER5Z1NJJTY6NGYMRW%3A%3AeyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdXRoMHx1c2VyXzAxSlhXVk0wRkVSNVoxTkpKVFk2TkdZTVJXIiwidGltZSI6IjE3NTMzMjE0NTkiLCJyYW5kb21uZXNzIjoiNTFkNjU0ZmMtMzBlNC00NjA2IiwiZXhwIjoxNzU4NTA1NDU5LCJpc3MiOiJodHRwczovL2F1dGhlbnRpY2F0aW9uLmN1cnNvci5zaCIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgb2ZmbGluZV9hY2Nlc3MiLCJhdWQiOiJodHRwczovL2N1cnNvci5jb20iLCJ0eXBlIjoid2ViIn0.w6yuj6QEZwvn5D1FggCWwlOzyFVWV0A1T0-e3Rjh9Uw'
        }

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://cursor.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Content-Type': 'application/json',
        }

        # 报警阈值（默认超过2个session就报警）
        self.alert_threshold = 2

        # 授权的session白名单（这些session不会被自动撤销）
        self.authorized_sessions = {
            'bef44cb7a943c9ebe9c1a770e3607a0755fec16743ebdd4d7846083bb0b80b2e',
            '25555cc17973482b42fa112a896973a3e49dfe3f494fd5a9037e72f105a0b4a9'
        }

        # session类型映射
        self.session_type_map = {
            'SESSION_TYPE_WEB': 1,
            'SESSION_TYPE_CLIENT': 2
        }

    def get_active_sessions(self):
        """
        获取当前活跃的cursor sessions
        """
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 正在获取cursor活跃sessions...")

            response = requests.get(
                self.api_url,
                cookies=self.cookies,
                headers=self.headers,
                timeout=30
            )

            print(f"请求状态码: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'session_count': len(data) if isinstance(data, list) else len(data.get('sessions', [])) if isinstance(data, dict) else 0
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'JSON解析失败',
                        'raw_response': response.text
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}',
                    'response_text': response.text
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'请求异常: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'未知错误: {str(e)}'
            }

    def revoke_session(self, session_id, session_type):
        """
        撤销指定的session
        """
        try:
            # 获取数值类型
            type_value = self.session_type_map.get(session_type, 1)

            payload = {
                "session_id": session_id,
                "type": type_value
            }

            print(f"正在撤销session: {session_id[:16]}... (类型: {session_type})")

            response = requests.post(
                self.revoke_url,
                cookies=self.cookies,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            print(f"撤销请求状态码: {response.status_code}")
            print(f"撤销响应: {response.text}")

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'成功撤销session: {session_id[:16]}...'
                }
            else:
                return {
                    'success': False,
                    'error': f'撤销失败 (HTTP {response.status_code}): {response.text}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'撤销session时发生错误: {str(e)}'
            }

    def analyze_sessions(self, sessions_data):
        """
        分析sessions，识别需要撤销的非授权session
        """
        if isinstance(sessions_data, list):
            sessions = sessions_data
        elif isinstance(sessions_data, dict) and 'sessions' in sessions_data:
            sessions = sessions_data['sessions']
        else:
            return [], []

        authorized = []
        unauthorized = []

        for session in sessions:
            session_id = session.get('sessionId', '')
            if session_id in self.authorized_sessions:
                authorized.append(session)
            else:
                unauthorized.append(session)

        return authorized, unauthorized

    def format_session_info(self, sessions_data):
        """
        格式化session信息用于显示
        """
        if isinstance(sessions_data, list):
            sessions = sessions_data
        elif isinstance(sessions_data, dict) and 'sessions' in sessions_data:
            sessions = sessions_data['sessions']
        else:
            return f"会话数据格式: {type(sessions_data).__name__}\n内容: {json.dumps(sessions_data, indent=2, ensure_ascii=False)}"

        if not sessions:
            return "没有发现活跃会话"

        authorized, unauthorized = self.analyze_sessions(sessions_data)

        info_lines = [f"发现 {len(sessions)} 个活跃会话:"]
        info_lines.append("-" * 60)

        if authorized:
            info_lines.append(f"✅ 授权会话 ({len(authorized)}个):")
            for i, session in enumerate(authorized, 1):
                info_lines.append(f"  会话 {i}:")
                if isinstance(session, dict):
                    for key, value in session.items():
                        info_lines.append(f"    {key}: {value}")
                info_lines.append("")

        if unauthorized:
            info_lines.append(f"⚠️  未授权会话 ({len(unauthorized)}个):")
            for i, session in enumerate(unauthorized, 1):
                info_lines.append(f"  会话 {i}:")
                if isinstance(session, dict):
                    for key, value in session.items():
                        info_lines.append(f"    {key}: {value}")
                info_lines.append("")

        return "\n".join(info_lines)

    def send_alert(self, message):
        """
        发送macOS桌面通知报警
        """
        try:
            # 转义消息中的特殊字符
            escaped_message = message.replace('"', '\\"').replace("'", "\\'")

            # 使用osascript发送通知
            script = f'''
            osascript -e 'display notification "{escaped_message}" with title "🚨 Cursor Session 报警" sound name "Basso"'
            '''

            print(f"发送报警通知: {message}")
            os.system(script)

            # 同时输出到控制台
            print("=" * 60)
            print("🚨 CURSOR SESSION 报警 🚨")
            print("=" * 60)
            print(message)
            print("=" * 60)

        except Exception as e:
            print(f"发送报警失败: {str(e)}")

    def monitor(self, strict_mode=False):
        """
        执行监测逻辑
        :param strict_mode: 严格模式，忽略阈值，只要有未授权session就撤销
        """
        if strict_mode:
            print("🔒 严格模式监测：任何未授权会话都将被立即撤销")
            print(f"授权会话白名单: {len(self.authorized_sessions)} 个")
        else:
            print(f"开始监测cursor会话 (报警阈值: {self.alert_threshold})")
            print(f"授权会话白名单: {len(self.authorized_sessions)} 个")

        # 获取session数据
        result = self.get_active_sessions()

        if result['success']:
            session_count = result['session_count']
            sessions_info = self.format_session_info(result['data'])

            print(f"\n当前活跃会话数量: {session_count}")
            print(f"详细信息:\n{sessions_info}")

            # 分析sessions
            authorized, unauthorized = self.analyze_sessions(result['data'])

            print(f"\n📊 会话分析:")
            print(f"  授权会话: {len(authorized)} 个")
            print(f"  未授权会话: {len(unauthorized)} 个")

            # 严格模式：只要有未授权session就撤销
            if strict_mode:
                if unauthorized:
                    alert_message = f"严格模式: 发现 {len(unauthorized)} 个未授权会话，正在立即撤销..."
                    self.send_alert(alert_message)

                    # 自动撤销未授权session
                    revoke_results = []
                    for session in unauthorized:
                        session_id = session.get('sessionId', '')
                        session_type = session.get('type', '')

                        print(f"\n🔒 正在撤销未授权会话: {session_id[:16]}...")
                        revoke_result = self.revoke_session(session_id, session_type)
                        revoke_results.append({
                            'session': session,
                            'result': revoke_result
                        })

                        if revoke_result['success']:
                            print(f"✅ {revoke_result['message']}")
                        else:
                            print(f"❌ 撤销失败: {revoke_result['error']}")

                    # 记录详细信息到日志文件
                    self.log_alert(session_count, sessions_info, revoke_results)

                    # 发送撤销完成通知
                    success_count = sum(1 for r in revoke_results if r['result']['success'])
                    final_message = f"严格模式撤销完成! 成功撤销 {success_count}/{len(unauthorized)} 个未授权会话"
                    self.send_alert(final_message)
                else:
                    print("✅ 严格模式检查通过：所有会话都在白名单中")

            # 普通模式：考虑阈值
            else:
                # 检查是否需要报警和自动撤销
                if session_count > self.alert_threshold:
                    alert_message = f"检测到异常! 当前有 {session_count} 个活跃会话，超过阈值 {self.alert_threshold}!"

                    if unauthorized:
                        alert_message += f" 发现 {len(unauthorized)} 个未授权会话，正在自动撤销..."
                        self.send_alert(alert_message)

                        # 自动撤销未授权session
                        revoke_results = []
                        for session in unauthorized:
                            session_id = session.get('sessionId', '')
                            session_type = session.get('type', '')

                            print(f"\n🔒 正在撤销未授权会话: {session_id[:16]}...")
                            revoke_result = self.revoke_session(session_id, session_type)
                            revoke_results.append({
                                'session': session,
                                'result': revoke_result
                            })

                            if revoke_result['success']:
                                print(f"✅ {revoke_result['message']}")
                            else:
                                print(f"❌ 撤销失败: {revoke_result['error']}")

                        # 记录详细信息到日志文件
                        self.log_alert(session_count, sessions_info, revoke_results)

                        # 发送撤销完成通知
                        success_count = sum(1 for r in revoke_results if r['result']['success'])
                        final_message = f"自动撤销完成! 成功撤销 {success_count}/{len(unauthorized)} 个未授权会话"
                        self.send_alert(final_message)

                    else:
                        self.send_alert(alert_message)
                        self.log_alert(session_count, sessions_info, [])

                else:
                    print(f"✅ 会话数量正常 ({session_count} <= {self.alert_threshold})")
                    if unauthorized:
                        print(f"⚠️  但发现 {len(unauthorized)} 个未授权会话，建议手动检查或使用严格模式")
        else:
            error_message = f"获取会话信息失败: {result['error']}"
            print(f"❌ {error_message}")
            self.send_alert(error_message)

    def log_alert(self, session_count, sessions_info, revoke_results=None):
        """
        将报警信息记录到日志文件
        """
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            log_file = os.path.join(log_dir, "cursor_session_alerts.log")
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"报警时间: {timestamp}\n")
                f.write(f"会话数量: {session_count}\n")
                f.write(f"阈值: {self.alert_threshold}\n")
                f.write(f"授权会话数量: {len(self.authorized_sessions)}\n")
                f.write(f"详细信息:\n{sessions_info}\n")

                if revoke_results:
                    f.write(f"\n🔒 自动撤销操作记录:\n")
                    for i, revoke_info in enumerate(revoke_results, 1):
                        session = revoke_info['session']
                        result = revoke_info['result']
                        session_id = session.get('sessionId', '')[:16]

                        f.write(f"  撤销 {i}: {session_id}... ")
                        if result['success']:
                            f.write("✅ 成功\n")
                        else:
                            f.write(f"❌ 失败 - {result['error']}\n")

                f.write(f"{'='*80}\n")

            print(f"📝 报警信息已记录到: {log_file}")

        except Exception as e:
            print(f"记录日志失败: {str(e)}")

def main():
    """
    主函数
    """
    monitor = CursorSessionMonitor()
    strict_mode = False

    # 解析命令行参数
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.lower() in ['--strict', '-s', 'strict']:
                strict_mode = True
                print("🔒 启用严格模式：忽略阈值，清理所有未授权会话")
            else:
                try:
                    monitor.alert_threshold = int(arg)
                    print(f"设置报警阈值为: {monitor.alert_threshold}")
                except ValueError:
                    print(f"忽略无效参数: {arg}")

    monitor.monitor(strict_mode)

if __name__ == "__main__":
    main()
