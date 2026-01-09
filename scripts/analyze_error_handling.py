#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误处理分析脚本

分析代码库中所有 try-catch 块的处理方式，生成分析报告。
"""

import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import json


class ErrorHandlingAnalyzer:
    """错误处理分析器"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.stats = {
            'frontend': defaultdict(int),
            'backend': defaultdict(int),
            'issues': [],
            'patterns': defaultdict(int)
        }
    
    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return {}
        
        is_frontend = 'frontend' in str(file_path)
        is_backend = 'app' in str(file_path) and file_path.suffix == '.py'
        
        if not (is_frontend or is_backend):
            return {}
        
        stats = {
            'try_blocks': 0,
            'empty_catch': 0,
            'console_error_only': 0,
            'print_error_only': 0,
            'no_user_feedback': 0,
            'no_logging': 0,
            'patterns': []
        }
        
        # 分析 try-catch 块
        if is_frontend:
            stats.update(self._analyze_frontend_file(content, file_path))
        elif is_backend:
            stats.update(self._analyze_backend_file(content, file_path))
        
        return stats
    
    def _analyze_frontend_file(self, content: str, file_path: Path) -> Dict:
        """分析前端文件"""
        stats = {
            'try_blocks': 0,
            'empty_catch': 0,
            'console_error_only': 0,
            'no_user_feedback': 0,
            'patterns': []
        }
        
        # 改进的正则：匹配 try { ... } catch (...) { ... } 块（支持多行和嵌套）
        # 使用更简单的方法：找到所有 try 关键字，然后找到对应的 catch
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if 'try' in line and '{' in line:
                # 找到 try 块
                try_start = i
                brace_count = 0
                in_try = False
                catch_start = -1
                
                # 查找对应的 catch
                j = i
                while j < len(lines):
                    current_line = lines[j]
                    
                    # 计算大括号
                    for char in current_line:
                        if char == '{':
                            brace_count += 1
                            if brace_count == 1:
                                in_try = True
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0 and in_try:
                                # try 块结束，查找 catch
                                if j + 1 < len(lines) and 'catch' in lines[j + 1]:
                                    catch_start = j + 1
                                    break
                    
                    if catch_start != -1:
                        break
                    j += 1
                
                if catch_start != -1:
                    # 提取 catch 块内容
                    catch_line = lines[catch_start]
                    if '{' in catch_line:
                        # catch 在同一行
                        catch_body_start = catch_start
                        catch_brace_count = 0
                        catch_end = catch_start
                        
                        for k in range(catch_start, len(lines)):
                            for char in lines[k]:
                                if char == '{':
                                    catch_brace_count += 1
                                elif char == '}':
                                    catch_brace_count -= 1
                                    if catch_brace_count == 0:
                                        catch_end = k
                                        break
                            if catch_brace_count == 0:
                                break
                        
                        # 提取 catch 块内容
                        catch_body_lines = lines[catch_body_start:catch_end + 1]
                        catch_body = '\n'.join(catch_body_lines)
                        
                        # 提取 catch 块内部内容（去掉 catch (...) { 和 }）
                        catch_inner = re.search(r'catch\s*\([^)]+\)\s*\{([^}]*)\}', catch_body, re.DOTALL)
                        if not catch_inner:
                            # 多行情况
                            catch_inner_match = re.search(r'catch\s*\([^)]+\)\s*\{', catch_body)
                            if catch_inner_match:
                                start_pos = catch_inner_match.end()
                                # 找到最后一个 }
                                last_brace = catch_body.rfind('}')
                                if last_brace > start_pos:
                                    catch_inner_text = catch_body[start_pos:last_brace].strip()
                                else:
                                    catch_inner_text = catch_body[start_pos:].strip()
                            else:
                                catch_inner_text = ''
                        else:
                            catch_inner_text = catch_inner.group(1).strip()
                        
                        stats['try_blocks'] += 1
                        
                        # 检查是否为空 catch
                        if not catch_inner_text or re.match(r'^\s*(//.*)?$', catch_inner_text, re.MULTILINE):
                            stats['empty_catch'] += 1
                            stats['patterns'].append({
                                'file': str(file_path.relative_to(self.root_dir)),
                                'line': try_start + 1,
                                'type': 'empty_catch',
                                'code': '\n'.join(lines[try_start:min(catch_end + 1, try_start + 5)])
                            })
                            i = catch_end + 1
                            continue
                        
                        # 只有 console.error
                        if re.search(r'console\.(error|warn)', catch_inner_text) and not re.search(r'(alert|toast|handleApiError|setError|showError)', catch_inner_text):
                            stats['console_error_only'] += 1
                            stats['patterns'].append({
                                'file': str(file_path.relative_to(self.root_dir)),
                                'line': try_start + 1,
                                'type': 'console_error_only',
                                'code': '\n'.join(lines[try_start:min(catch_end + 1, try_start + 5)])
                            })
                        
                        # 没有用户反馈
                        if not re.search(r'(alert|toast|handleApiError|setError|showError|message)', catch_inner_text, re.IGNORECASE):
                            stats['no_user_feedback'] += 1
                        
                        i = catch_end + 1
                        continue
            
            i += 1
        
        return stats
    
    def _analyze_backend_file(self, content: str, file_path: Path) -> Dict:
        """分析后端文件"""
        stats = {
            'try_blocks': 0,
            'empty_except': 0,
            'print_error_only': 0,
            'no_logging': 0,
            'patterns': []
        }
        
        # 匹配 try-except 块
        try_except_pattern = r'try\s*:.*?except\s+.*?:'
        matches = re.finditer(try_except_pattern, content, re.DOTALL)
        
        for match in matches:
            stats['try_blocks'] += 1
            except_block = match.group(0)
            
            # 提取 except 块内容
            except_match = re.search(r'except\s+.*?:\s*(.*?)(?=\n\s*(?:except|else|finally|def|class|\Z))', except_block, re.DOTALL)
            if except_match:
                except_body = except_match.group(1).strip()
                
                # 空 except 或只有 pass
                if not except_body or except_body.strip() == 'pass':
                    stats['empty_except'] += 1
                    stats['patterns'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': content[:match.start()].count('\n') + 1,
                        'type': 'empty_except',
                        'code': except_block[:200]
                    })
                    continue
                
                # 只有 print
                if re.search(r'print\s*\(', except_body) and not re.search(r'logger\.', except_body):
                    stats['print_error_only'] += 1
                    stats['patterns'].append({
                        'file': str(file_path.relative_to(self.root_dir)),
                        'line': content[:match.start()].count('\n') + 1,
                        'type': 'print_error_only',
                        'code': except_block[:200]
                    })
                
                # 没有日志记录
                if not re.search(r'logger\.(error|warning|info|exception)', except_body):
                    stats['no_logging'] += 1
        
        return stats
    
    def analyze(self) -> Dict:
        """分析整个代码库"""
        total_stats = {
            'frontend': defaultdict(int),
            'backend': defaultdict(int),
            'issues': []
        }
        
        # 分析前端文件
        frontend_dir = self.root_dir / 'frontend' / 'src'
        if frontend_dir.exists():
            for file_path in frontend_dir.rglob('*.{js,jsx,ts,tsx}'):
                if 'node_modules' in str(file_path):
                    continue
                stats = self._analyze_frontend_file(
                    file_path.read_text(encoding='utf-8'),
                    file_path
                )
                for key, value in stats.items():
                    if isinstance(value, int):
                        total_stats['frontend'][key] += value
                    elif isinstance(value, list):
                        total_stats['issues'].extend(value)
        
        # 分析后端文件
        backend_dir = self.root_dir / 'app'
        if backend_dir.exists():
            for file_path in backend_dir.rglob('*.py'):
                stats = self._analyze_backend_file(
                    file_path.read_text(encoding='utf-8'),
                    file_path
                )
                for key, value in stats.items():
                    if isinstance(value, int):
                        total_stats['backend'][key] += value
                    elif isinstance(value, list):
                        total_stats['issues'].extend(value)
        
        return total_stats
    
    def generate_report(self, stats: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append("# 错误处理分析报告\n")
        
        # 统计摘要
        report.append("## 统计摘要\n")
        report.append(f"- 前端 try-catch 块: {stats['frontend']['try_blocks']}")
        report.append(f"- 后端 try-except 块: {stats['backend']['try_blocks']}")
        report.append(f"- 总计: {stats['frontend']['try_blocks'] + stats['backend']['try_blocks']}\n")
        
        # 前端问题
        report.append("## 前端问题统计\n")
        report.append(f"- 空 catch 块: {stats['frontend']['empty_catch']}")
        report.append(f"- 只有 console.error: {stats['frontend']['console_error_only']}")
        report.append(f"- 没有用户反馈: {stats['frontend']['no_user_feedback']}\n")
        
        # 后端问题
        report.append("## 后端问题统计\n")
        report.append(f"- 空 except 块: {stats['backend']['empty_except']}")
        report.append(f"- 只有 print: {stats['backend']['print_error_only']}")
        report.append(f"- 没有日志记录: {stats['backend']['no_logging']}\n")
        
        # 问题详情
        if stats['issues']:
            report.append("## 问题详情\n")
            
            # 按类型分组
            issues_by_type = defaultdict(list)
            for issue in stats['issues']:
                issues_by_type[issue['type']].append(issue)
            
            for issue_type, issues in issues_by_type.items():
                report.append(f"\n### {issue_type} ({len(issues)} 个)\n")
                for issue in issues[:10]:  # 只显示前10个
                    report.append(f"- `{issue['file']}:{issue['line']}`")
                    report.append(f"  ```\n  {issue['code'][:100]}...\n  ```\n")
                if len(issues) > 10:
                    report.append(f"- ... 还有 {len(issues) - 10} 个类似问题\n")
        
        return '\n'.join(report)


def main():
    """主函数"""
    import sys
    
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    analyzer = ErrorHandlingAnalyzer(root_dir)
    stats = analyzer.analyze()
    
    # 生成报告
    report = analyzer.generate_report(stats)
    print(report)
    
    # 保存 JSON 报告
    output_file = Path(root_dir) / 'error_handling_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {output_file}")


if __name__ == '__main__':
    main()
