#!/usr/bin/env python3
"""
Wiki内容清理功能测试脚本

功能：
- 测试清理规则是否正确应用
- 验证文件大小变化
- 检查链接转换效果

用法：
    python scripts/test_cleanup.py --character neuvillette
    python scripts/test_cleanup.py --all
"""

import argparse
import re
from pathlib import Path
from typing import Dict, List


def test_cleanup_rules(file_path: Path) -> Dict:
    """
    测试清理规则
    
    Args:
        file_path: Wiki文件路径
        
    Returns:
        测试结果字典
    """
    if not file_path.exists():
        return {'error': f'文件不存在：{file_path}'}
    
    content = file_path.read_text(encoding='utf-8')
    
    results = {
        'file': str(file_path),
        'size_kb': file_path.stat().st_size / 1024,  # 使用文件系统统计的大小
        'lines': len(content.splitlines()),
        'checks': {}
    }
    
    # 检查1：导航模板是否被删除
    nav_template = re.search(r'\|\s*\[查\]\([^)]*Template[^)]*\)', content)
    results['checks']['navigation_template_removed'] = {
        'status': '✅ 通过' if not nav_template else '❌ 失败',
        'found': bool(nav_template)
    }
    
    # 检查2：JSON-LD是否被删除
    json_ld = re.search(r'```json\n.*?\n```', content, re.DOTALL)
    results['checks']['json_ld_removed'] = {
        'status': '✅ 通过' if not json_ld else '❌ 失败',
        'found': bool(json_ld)
    }
    
    # 检查3：内部链接是否被转换
    internal_links = re.findall(r'「([^」]+)」', content)
    results['checks']['internal_links_converted'] = {
        'status': f'✅ 通过 ({len(internal_links)}处)' if internal_links else '⚠️ 未找到',
        'count': len(internal_links)
    }
    
    # 检查4：脚注引用是否保留
    footnote_refs = re.findall(r'\[.*?\]\(#cite', content)
    results['checks']['footnote_refs_preserved'] = {
        'status': f'✅ 通过 ({len(footnote_refs)}处)' if footnote_refs else '⚠️ 未找到',
        'count': len(footnote_refs)
    }
    
    # 检查5：外部链接是否保留
    external_links = re.findall(r'\[.*?\]\(https?://', content)
    results['checks']['external_links_preserved'] = {
        'status': f'✅ 通过 ({len(external_links)}处)' if external_links else '⚠️ 未找到',
        'count': len(external_links)
    }
    
    # 检查6：注释章节是否保留
    reference_section = '## 注释及外部链接' in content
    results['checks']['reference_section_preserved'] = {
        'status': '✅ 通过' if reference_section else '❌ 失败',
        'found': reference_section
    }
    
    # 检查7：Lorem ipsum占位符是否被删除
    lorem_ipsum = re.search(r'Lorem ipsum', content, re.IGNORECASE)
    results['checks']['lorem_ipsum_removed'] = {
        'status': '✅ 通过' if not lorem_ipsum else '❌ 失败',
        'found': bool(lorem_ipsum)
    }
    
    # 检查8：技能倍率表格是否被删除
    skill_table = re.search(r'\|\s*详细属性', content)
    level_marker = re.search(r'Lv\.\d+', content)
    results['checks']['skill_tables_removed'] = {
        'status': '✅ 通过' if not skill_table and not level_marker else '❌ 失败',
        'found': bool(skill_table or level_marker)
    }
    
    return results


def print_results(results: Dict) -> None:
    """打印测试结果"""
    print(f"\n{'='*60}")
    print(f"文件：{results['file']}")
    print(f"{'='*60}")
    print(f"大小：{results['size_kb']:.1f} KB")
    print(f"行数：{results['lines']} 行")
    print(f"\n检查结果：")
    
    for check_name, check_result in results['checks'].items():
        print(f"  {check_result['status']} - {check_name.replace('_', ' ')}")
    
    # 统计通过率
    passed = sum(1 for c in results['checks'].values() if '✅' in c['status'])
    total = len(results['checks'])
    
    print(f"\n通过率：{passed}/{total} ({passed/total*100:.0f}%)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Wiki内容清理功能测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 测试单个角色
    python scripts/test_cleanup.py --character neuvillette
    
    # 测试所有角色
    python scripts/test_cleanup.py --all
        """
    )
    
    parser.add_argument('--character', type=str, help='角色目录名称')
    parser.add_argument('--all', action='store_true', help='测试所有角色')
    
    args = parser.parse_args()
    
    base_dir = Path('characters')
    
    if args.all:
        # 测试所有角色
        if not base_dir.exists():
            print("错误：characters 目录不存在")
            return
        
        character_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        
        if not character_dirs:
            print("错误：未找到任何角色目录")
            return
        
        all_results = []
        for char_dir in character_dirs:
            wiki_file = char_dir / 'wiki.md'
            if wiki_file.exists():
                results = test_cleanup_rules(wiki_file)
                all_results.append(results)
                print_results(results)
        
        # 汇总
        print(f"\n{'='*60}")
        print("汇总报告")
        print(f"{'='*60}")
        print(f"测试角色数：{len(all_results)}")
        
        if all_results:
            avg_size = sum(r['size_kb'] for r in all_results) / len(all_results)
            avg_lines = sum(r['lines'] for r in all_results) / len(all_results)
            print(f"平均文件大小：{avg_size:.1f} KB")
            print(f"平均行数：{avg_lines:.0f} 行")
    
    elif args.character:
        # 测试单个角色
        char_dir = base_dir / args.character
        wiki_file = char_dir / 'wiki.md'
        
        results = test_cleanup_rules(wiki_file)
        
        if 'error' in results:
            print(f"错误：{results['error']}")
            return
        
        print_results(results)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
