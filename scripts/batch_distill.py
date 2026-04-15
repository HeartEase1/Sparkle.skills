#!/usr/bin/env python3
"""
批量处理脚本

功能：
- 批量获取多个角色的 Wiki 内容
- 批量质量检查
- 生成汇总报告

用法：
    python scripts/batch_distill.py --game genshin --characters 芙宁娜,钟离,胡桃(原神)
    python scripts/batch_distill.py --input characters.txt
    python scripts/batch_distill.py --check-all
"""

import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


def run_command(cmd: List[str], cwd: str = None) -> Dict:
    """
    运行命令并返回结果
    
    Args:
        cmd: 命令列表
        cwd: 工作目录
        
    Returns:
        包含 success、output、error 的字典
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=cwd
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': '命令超时',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': str(e),
            'returncode': -1
        }


def batch_fetch_wiki(game: str, wiki: str, characters: List[str], output_dir: Path) -> Dict:
    """
    批量获取 Wiki 内容
    
    Args:
        game: 游戏标识
        wiki: Wiki 标识
        characters: 角色列表
        output_dir: 输出目录
        
    Returns:
        汇总结果
    """
    results = []
    
    for character in characters:
        print(f"\n{'='*60}")
        print(f"获取角色：{character}")
        print(f"{'='*60}")
        
        output_path = output_dir / character / 'wiki.md'
        
        cmd = [
            'python', 'scripts/fetch_wiki.py',
            '--game', game,
            '--wiki', wiki,
            '--character', character,
            '--output', str(output_path)
        ]
        
        result = run_command(cmd)
        
        results.append({
            'character': character,
            'success': result['success'],
            'output_path': str(output_path),
            'error': result['error'] if not result['success'] else None
        })
    
    # 汇总
    success_count = sum(1 for r in results if r['success'])
    
    return {
        'total': len(characters),
        'success': success_count,
        'failed': len(characters) - success_count,
        'results': results
    }


def batch_quality_check(characters: List[str], output_dir: Path) -> Dict:
    """
    批量质量检查
    
    Args:
        characters: 角色列表
        output_dir: 输出目录
        
    Returns:
        汇总结果
    """
    results = []
    
    for character in characters:
        print(f"\n{'='*60}")
        print(f"检查角色：{character}")
        print(f"{'='*60}")
        
        character_dir = output_dir / character
        
        cmd = [
            'python', 'scripts/quality_check.py',
            '--character', character
        ]
        
        result = run_command(cmd)
        
        if result['success']:
            # 解析输出，提取评分
            output = result['output']
            score = None
            rating = None
            
            for line in output.splitlines():
                if '综合评分' in line:
                    # 提取评分
                    import re
                    match = re.search(r'(\d+\.\d+)', line)
                    if match:
                        score = float(match.group(1))
                elif '评级' in line and '⭐' in line:
                    rating = line.split('：')[-1].strip()
            
            results.append({
                'character': character,
                'success': True,
                'score': score,
                'rating': rating
            })
        else:
            results.append({
                'character': character,
                'success': False,
                'score': None,
                'rating': None,
                'error': result['error']
            })
    
    # 汇总
    success_count = sum(1 for r in results if r['success'])
    scores = [r['score'] for r in results if r['score'] is not None]
    
    return {
        'total': len(characters),
        'success': success_count,
        'failed': len(characters) - success_count,
        'average_score': sum(scores) / len(scores) if scores else 0,
        'results': results
    }


def generate_summary_report(fetch_results: Dict, check_results: Dict, output_path: Path) -> str:
    """
    生成汇总报告
    
    Args:
        fetch_results: Wiki 获取结果
        check_results: 质量检查结果
        output_path: 输出路径
        
    Returns:
        报告内容
    """
    report = f"""# 批量处理报告

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Wiki 获取结果

- **总数**：{fetch_results['total']}
- **成功**：{fetch_results['success']}
- **失败**：{fetch_results['failed']}

| 角色 | 状态 | 输出路径 | 错误 |
|------|------|----------|------|
"""

    for result in fetch_results['results']:
        status = '✅' if result['success'] else '❌'
        error = result['error'] if result['error'] else '-'
        report += f"| {result['character']} | {status} | {result['output_path']} | {error} |\n"
    
    report += f"""
---

## 质量检查结果

- **总数**：{check_results['total']}
- **成功**：{check_results['success']}
- **失败**：{check_results['failed']}
- **平均评分**：{check_results['average_score']:.3f}

| 角色 | 状态 | 评分 | 评级 |
|------|------|------|------|
"""

    for result in check_results['results']:
        status = '✅' if result['success'] else '❌'
        score = f"{result['score']:.3f}" if result['score'] else '-'
        rating = result['rating'] if result['rating'] else '-'
        report += f"| {result['character']} | {status} | {score} | {rating} |\n"
    
    report += """
---

## 建议

"""
    
    # 生成建议
    failed_fetch = [r for r in fetch_results['results'] if not r['success']]
    if failed_fetch:
        report += "### Wiki 获取失败\n"
        for result in failed_fetch:
            report += f"- {result['character']}：{result['error']}\n"
        report += "\n"
    
    low_score = [r for r in check_results['results'] if r['score'] and r['score'] < 0.7]
    if low_score:
        report += "### 质量评分较低\n"
        for result in low_score:
            report += f"- {result['character']}：{result['score']:.3f}（建议补充设定材料）\n"
    
    if not failed_fetch and not low_score:
        report += "✅ 所有角色处理成功，质量良好。\n"
    
    # 保存报告
    output_path.write_text(report, encoding='utf-8')
    
    return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='批量处理脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 批量获取 Wiki 内容
    python scripts/batch_distill.py --game genshin --wiki moegirl --characters 芙宁娜,钟离,胡桃(原神)
    
    # 从文件读取角色列表
    python scripts/batch_distill.py --game genshin --wiki moegirl --input characters.txt
    
    # 批量质量检查
    python scripts/batch_distill.py --check-all
    
    # 完整流程（获取 + 检查）
    python scripts/batch_distill.py --game genshin --wiki moegirl --characters 芙宁娜,钟离 --full
        """
    )
    
    parser.add_argument('--game', help='游戏标识（genshin/hsr/deltaforce）')
    parser.add_argument('--wiki', default='moegirl', help='Wiki 标识（默认 moegirl）')
    parser.add_argument('--characters', help='角色列表（逗号分隔）')
    parser.add_argument('--input', help='角色列表文件')
    parser.add_argument('--output-dir', default='characters', help='输出目录')
    parser.add_argument('--check-all', action='store_true', help='检查所有角色')
    parser.add_argument('--full', action='store_true', help='完整流程（获取 + 检查）')
    parser.add_argument('--report', help='报告输出路径')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    # 读取角色列表
    characters = []
    
    if args.characters:
        characters = [c.strip() for c in args.characters.split(',')]
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误：文件不存在：{input_path}")
            return
        characters = [line.strip() for line in input_path.read_text().splitlines() if line.strip()]
    elif args.check_all:
        # 检查所有角色
        if not output_dir.exists():
            print(f"错误：目录不存在：{output_dir}")
            return
        characters = [d.name for d in output_dir.iterdir() if d.is_dir()]
    else:
        parser.print_help()
        return
    
    if not characters:
        print("错误：未指定任何角色")
        return
    
    print(f"待处理角色：{', '.join(characters)}")
    
    # 执行流程
    fetch_results = None
    check_results = None
    
    if args.game:
        # 获取 Wiki
        print("\n" + "="*60)
        print("Phase 1: 获取 Wiki 内容")
        print("="*60)
        fetch_results = batch_fetch_wiki(args.game, args.wiki, characters, output_dir)
    
    if args.check_all or args.full:
        # 质量检查
        print("\n" + "="*60)
        print("Phase 2: 质量检查")
        print("="*60)
        check_results = batch_quality_check(characters, output_dir)
    
    # 生成报告
    if fetch_results or check_results:
        print("\n" + "="*60)
        print("生成汇总报告")
        print("="*60)
        
        report_path = Path(args.report) if args.report else output_dir / 'batch_report.md'
        
        # 如果只有部分结果，补充默认值
        if fetch_results is None:
            fetch_results = {'total': 0, 'success': 0, 'failed': 0, 'results': []}
        if check_results is None:
            check_results = {'total': 0, 'success': 0, 'failed': 0, 'average_score': 0, 'results': []}
        
        report = generate_summary_report(fetch_results, check_results, report_path)
        
        print(f"\n报告已保存到：{report_path}")


if __name__ == '__main__':
    main()
