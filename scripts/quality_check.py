#!/usr/bin/env python3
"""
质量评分脚本

功能：
- 扫描角色目录，统计证据数量
- 计算质量评分（完整度 + 证据率 + 冲突数 + 测试通过率）
- 生成质量报告

用法：
    python scripts/quality_check.py --character <角色目录>
    python scripts/quality_check.py --character furina-demo
    python scripts/quality_check.py --character furina-demo --output report.md
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 维度文件列表
DIMENSION_FILES = [
    'profile.md',
    'personality.md', 
    'interaction.md',
    'memory.md',
    'relations.md'
]


def count_evidence(content: str) -> Dict[str, int]:
    """
    统计文件中的证据数量
    
    Args:
        content: Markdown 文件内容
        
    Returns:
        包含 verbatim、artifact、impression、total 的字典
    """
    verbatim = len(re.findall(r'`verbatim`', content))
    artifact = len(re.findall(r'`artifact`', content))
    impression = len(re.findall(r'`impression`', content))
    total = verbatim + artifact + impression
    
    return {
        'verbatim': verbatim,
        'artifact': artifact,
        'impression': impression,
        'total': total
    }


def is_non_empty_dimension(file_path: Path) -> bool:
    """
    判断维度文件是否非空（至少有3条有效内容且有证据标注）
    
    Args:
        file_path: 维度文件路径
        
    Returns:
        是否非空
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 统计证据数量
    evidence = count_evidence(content)
    
    # 至少有3条有效内容（以 - 或 > 开头的行，且有证据标注）
    # 简化判断：至少有3个证据标注
    return evidence['total'] >= 3


def count_conflicts(conflicts_file: Path) -> int:
    """
    统计冲突数量
    
    Args:
        conflicts_file: conflicts.md 文件路径
        
    Returns:
        冲突数量
    """
    if not conflicts_file.exists():
        return 0
    
    content = conflicts_file.read_text(encoding='utf-8')
    
    # 统计冲突标题数量（以 ## 开头的行，且不是"设定冲突记录"）
    conflict_headers = re.findall(r'^## (?!设定冲突记录)', content, re.MULTILINE)
    
    # 如果文件内容只有"目前未发现重大设定冲突"，返回0
    if '目前未发现重大设定冲突' in content:
        return 0
    
    return len(conflict_headers)


def get_conflict_score(conflict_count: int) -> float:
    """
    根据冲突数量计算得分
    
    Args:
        conflict_count: 冲突数量
        
    Returns:
        冲突得分（0-1）
    """
    if conflict_count == 0:
        return 1.0
    elif conflict_count <= 2:
        return 0.9
    elif conflict_count <= 5:
        return 0.7
    elif conflict_count <= 10:
        return 0.5
    else:
        return 0.3


def get_test_results(test_file: Path) -> Dict | None:
    """
    获取测试结果（如果存在）
    
    Args:
        test_file: 测试结果文件路径
        
    Returns:
        测试结果字典，如果不存在则返回 None
    """
    if not test_file.exists():
        return None
    
    try:
        content = test_file.read_text(encoding='utf-8')
        data = json.loads(content)
        return data
    except:
        return None


def calculate_quality_score(
    evidence_summary: Dict[str, int],
    dimension_status: Dict[str, bool],
    conflict_count: int,
    test_results: Dict | None = None
) -> Dict:
    """
    计算质量评分
    
    Args:
        evidence_summary: 证据统计
        dimension_status: 各维度状态
        conflict_count: 冲突数量
        test_results: 测试结果（可选）
        
    Returns:
        质量评分字典
    """
    # 1. 完整度（30%）
    non_empty_count = sum(1 for status in dimension_status.values() if status)
    completeness = non_empty_count / 5
    
    # 2. 证据率（40%）
    total = evidence_summary['total']
    if total > 0:
        evidence_ratio = (evidence_summary['verbatim'] + evidence_summary['artifact']) / total
    else:
        evidence_ratio = 0.0
    
    # 3. 冲突数得分（10%）
    conflict_score = get_conflict_score(conflict_count)
    
    # 4. 测试通过率（20%）
    if test_results and 'test_results' in test_results:
        test_scenarios = test_results['test_results'].get('scenarios', [])
        if test_scenarios:
            passed = sum(1 for s in test_scenarios if s.get('score', 0) >= 0.7)
            test_pass_rate = passed / len(test_scenarios)
        else:
            test_pass_rate = 0.0
    else:
        # 如果没有测试结果，按权重重新分配
        test_pass_rate = None
    
    # 5. 综合评分
    if test_pass_rate is not None:
        overall = (
            completeness * 0.3 +
            evidence_ratio * 0.4 +
            conflict_score * 0.1 +
            test_pass_rate * 0.2
        )
    else:
        # 没有测试结果，调整权重
        overall = (
            completeness * 0.4 +
            evidence_ratio * 0.5 +
            conflict_score * 0.1
        )
    
    # 6. 评级
    if overall >= 0.85:
        rating = '优秀'
        stars = '⭐⭐⭐⭐⭐'
    elif overall >= 0.70:
        rating = '良好'
        stars = '⭐⭐⭐⭐'
    elif overall >= 0.60:
        rating = '及格'
        stars = '⭐⭐⭐'
    else:
        rating = '不合格'
        stars = '⭐⭐'
    
    return {
        'completeness': round(completeness, 2),
        'evidence_ratio': round(evidence_ratio, 2),
        'conflict_count': conflict_count,
        'conflict_score': round(conflict_score, 2),
        'test_pass_rate': round(test_pass_rate, 2) if test_pass_rate is not None else None,
        'overall': round(overall, 3),
        'rating': rating,
        'stars': stars
    }


def generate_supplement_suggestions(
    quality_score: Dict,
    evidence_summary: Dict[str, int],
    dimension_status: Dict[str, bool]
) -> List[Dict]:
    """
    生成补充建议
    
    Args:
        quality_score: 质量评分
        evidence_summary: 证据统计
        dimension_status: 各维度状态
        
    Returns:
        补充建议列表
    """
    suggestions = []
    
    # 检查维度缺失
    for dimension, is_non_empty in dimension_status.items():
        if not is_non_empty:
            suggestions.append({
                'dimension': dimension.replace('.md', ''),
                'priority': '高',
                'reason': '维度文件缺失或内容不足',
                'suggestion': f'请补充 {dimension.replace(".md", "")} 相关的设定材料'
            })
    
    # 检查证据率
    if evidence_summary['total'] > 0:
        evidence_ratio = (evidence_summary['verbatim'] + evidence_summary['artifact']) / evidence_summary['total']
        if evidence_ratio < 0.5:
            suggestions.append({
                'dimension': '全部',
                'priority': '高',
                'reason': f'证据率仅 {evidence_ratio:.1%}，缺少官方设定支撑',
                'suggestion': '请提供更多角色台词、官方设定文本'
            })
    
    # 检查冲突数
    if quality_score['conflict_count'] > 5:
        suggestions.append({
            'dimension': 'conflicts.md',
            'priority': '中',
            'reason': f'存在 {quality_score["conflict_count"]} 个设定冲突',
            'suggestion': '建议明确采用哪个版本的设定'
        })
    
    # 检查测试通过率
    if quality_score['test_pass_rate'] is not None and quality_score['test_pass_rate'] < 0.7:
        suggestions.append({
            'dimension': '全部',
            'priority': '高',
            'reason': f'扮演测试通过率仅 {quality_score["test_pass_rate"]:.1%}',
            'suggestion': '建议补充设定材料后重新测试'
        })
    
    return suggestions


def generate_report(
    character_dir: Path,
    evidence_summary: Dict[str, int],
    dimension_status: Dict[str, bool],
    quality_score: Dict,
    suggestions: List[Dict]
) -> str:
    """
    生成 Markdown 格式的质量报告
    
    Args:
        character_dir: 角色目录
        evidence_summary: 证据统计
        dimension_status: 各维度状态
        quality_score: 质量评分
        suggestions: 补充建议
        
    Returns:
        Markdown 报告
    """
    report = f"""# 质量评分报告：{character_dir.name}

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**综合评分**：{quality_score['overall']} / 1.0
**评级**：{quality_score['rating']} {quality_score['stars']}

---

## 评分详情

| 维度 | 得分 | 权重 | 加权得分 | 评级 |
|------|------|------|----------|------|
| 完整度 | {quality_score['completeness']} | 30% | {quality_score['completeness'] * 0.3:.3f} | {'优秀' if quality_score['completeness'] >= 0.9 else '良好' if quality_score['completeness'] >= 0.7 else '及格'} |
| 证据率 | {quality_score['evidence_ratio']} | 40% | {quality_score['evidence_ratio'] * 0.4:.3f} | {'优秀' if quality_score['evidence_ratio'] >= 0.8 else '良好' if quality_score['evidence_ratio'] >= 0.7 else '及格'} |
| 冲突数 | {quality_score['conflict_score']} | 10% | {quality_score['conflict_score'] * 0.1:.3f} | {'优秀' if quality_score['conflict_count'] == 0 else '良好' if quality_score['conflict_count'] <= 2 else '及格'} |
"""

    if quality_score['test_pass_rate'] is not None:
        report += f"| 测试通过率 | {quality_score['test_pass_rate']} | 20% | {quality_score['test_pass_rate'] * 0.2:.3f} | {'优秀' if quality_score['test_pass_rate'] >= 0.9 else '良好' if quality_score['test_pass_rate'] >= 0.8 else '及格'} |\n"
    else:
        report += "| 测试通过率 | 未测试 | 20% | 0.000 | - |\n"
    
    report += f"\n**总评分**：{quality_score['overall']}\n"
    
    # 证据分布
    if evidence_summary['total'] > 0:
        verbatim_pct = f"{evidence_summary['verbatim'] / evidence_summary['total'] * 100:.1f}%"
        artifact_pct = f"{evidence_summary['artifact'] / evidence_summary['total'] * 100:.1f}%"
        impression_pct = f"{evidence_summary['impression'] / evidence_summary['total'] * 100:.1f}%"
    else:
        verbatim_pct = "0.0%"
        artifact_pct = "0.0%"
        impression_pct = "0.0%"
    
    report += f"""
---

## 证据分布

| 证据类型 | 数量 | 占比 |
|----------|------|------|
| verbatim（原话） | {evidence_summary['verbatim']} | {verbatim_pct} |
| artifact（设定） | {evidence_summary['artifact']} | {artifact_pct} |
| impression（评价） | {evidence_summary['impression']} | {impression_pct} |
| **总计** | **{evidence_summary['total']}** | **100%** |
"""
    
    # 维度覆盖情况
    report += """
---

## 维度覆盖情况

| 维度 | 状态 | 说明 |
|------|------|------|
"""
    
    for dimension_file, is_non_empty in dimension_status.items():
        dimension_name = dimension_file.replace('.md', '')
        status = '✅ 完整' if is_non_empty else '❌ 缺失'
        note = '至少有3条有效内容' if is_non_empty else '内容不足或文件缺失'
        report += f"| {dimension_name} | {status} | {note} |\n"
    
    # 建议
    if suggestions:
        report += """
---

## 补充建议

| 维度 | 优先级 | 问题 | 建议 |
|------|--------|------|------|
"""
        for suggestion in suggestions:
            report += f"| {suggestion['dimension']} | {suggestion['priority']} | {suggestion['reason']} | {suggestion['suggestion']} |\n"
    else:
        report += f"""
---

## 建议

✅ 质量优秀，可直接使用

角色设定完整，证据充足，扮演一致性高。建议定期检查游戏版本更新，如有新设定可增量更新。
"""
    
    return report


def check_character(character_dir: Path, output_file: Path | None = None) -> Dict:
    """
    检查角色质量并生成报告
    
    Args:
        character_dir: 角色目录路径
        output_file: 输出文件路径（可选）
        
    Returns:
        质量检查结果
    """
    # 检查目录是否存在
    if not character_dir.exists():
        raise FileNotFoundError(f"角色目录不存在：{character_dir}")
    
    # 1. 统计证据
    evidence_summary = {
        'verbatim': 0,
        'artifact': 0,
        'impression': 0,
        'total': 0
    }
    
    for dimension_file in DIMENSION_FILES:
        file_path = character_dir / dimension_file
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            evidence = count_evidence(content)
            evidence_summary['verbatim'] += evidence['verbatim']
            evidence_summary['artifact'] += evidence['artifact']
            evidence_summary['impression'] += evidence['impression']
            evidence_summary['total'] += evidence['total']
    
    # 2. 检查维度状态
    dimension_status = {}
    for dimension_file in DIMENSION_FILES:
        file_path = character_dir / dimension_file
        dimension_status[dimension_file] = is_non_empty_dimension(file_path)
    
    # 3. 统计冲突
    conflicts_file = character_dir / 'conflicts.md'
    conflict_count = count_conflicts(conflicts_file)
    
    # 4. 获取测试结果
    test_file = character_dir / 'test_results.json'
    test_results = get_test_results(test_file)
    
    # 5. 计算质量评分
    quality_score = calculate_quality_score(
        evidence_summary,
        dimension_status,
        conflict_count,
        test_results
    )
    
    # 6. 生成补充建议
    suggestions = generate_supplement_suggestions(
        quality_score,
        evidence_summary,
        dimension_status
    )
    
    # 7. 生成报告
    report = generate_report(
        character_dir,
        evidence_summary,
        dimension_status,
        quality_score,
        suggestions
    )
    
    # 8. 输出报告
    if output_file:
        output_file.write_text(report, encoding='utf-8')
        print(f"报告已保存到：{output_file}")
    else:
        print(report)
    
    # 9. 返回结果
    return {
        'character': character_dir.name,
        'evidence_summary': evidence_summary,
        'dimension_status': dimension_status,
        'quality_score': quality_score,
        'suggestions': suggestions,
        'report': report
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='质量评分脚本 - 检查角色蒸馏质量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 检查单个角色
    python scripts/quality_check.py --character furina-demo
    
    # 保存报告到文件
    python scripts/quality_check.py --character furina-demo --output report.md
    
    # 检查所有角色
    python scripts/quality_check.py --all
        """
    )
    
    parser.add_argument(
        '--character',
        type=str,
        help='角色目录名称（如 furina-demo）'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='检查所有角色'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='输出文件路径（Markdown 格式）'
    )
    
    parser.add_argument(
        '--json',
        type=str,
        help='输出 JSON 格式结果到文件'
    )
    
    args = parser.parse_args()
    
    # 确定要检查的角色
    base_dir = Path('characters')
    
    if args.all:
        # 检查所有角色
        if not base_dir.exists():
            print("错误：characters 目录不存在")
            return
        
        character_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        
        if not character_dirs:
            print("错误：未找到任何角色目录")
            return
        
        results = []
        for character_dir in character_dirs:
            print(f"\n{'='*60}")
            print(f"检查角色：{character_dir.name}")
            print(f"{'='*60}\n")
            
            try:
                result = check_character(character_dir)
                results.append(result)
            except Exception as e:
                print(f"错误：{e}")
        
        # 输出汇总
        print(f"\n{'='*60}")
        print("汇总报告")
        print(f"{'='*60}\n")
        
        for result in results:
            print(f"{result['character']}: {result['quality_score']['overall']} ({result['quality_score']['rating']})")
        
        # 保存 JSON 结果
        if args.json:
            import json
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"\nJSON 结果已保存到：{args.json}")
    
    elif args.character:
        # 检查单个角色
        character_dir = base_dir / args.character
        
        output_file = Path(args.output) if args.output else None
        
        result = check_character(character_dir, output_file)
        
        # 保存 JSON 结果
        if args.json:
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\nJSON 结果已保存到：{args.json}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
