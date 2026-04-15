#!/usr/bin/env python3
"""
manifest.json 生成脚本

功能：
- 生成符合规范的 manifest.json
- 验证 manifest.json 格式
- 更新现有 manifest.json

用法：
    python scripts/generate_manifest.py --character <角色名> --game <游戏名>
    python scripts/generate_manifest.py --character furina-demo --game "原神 Genshin Impact"
    python scripts/generate_manifest.py --validate manifest.json
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


def to_slug(name: str) -> str:
    """
    将角色名转换为 slug（小写字母、数字、连字符）
    
    Args:
        name: 角色名
        
    Returns:
        slug
    """
    # 转换为小写
    slug = name.lower()
    
    # 将空格和下划线替换为连字符
    slug = slug.replace(' ', '-').replace('_', '-')
    
    # 移除非字母数字字符（保留连字符）
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # 移除连续的连字符
    slug = re.sub(r'-+', '-', slug)
    
    # 移除开头和结尾的连字符
    slug = slug.strip('-')
    
    return slug


def validate_manifest(manifest: Dict) -> List[str]:
    """
    验证 manifest.json 格式
    
    Args:
        manifest: manifest 字典
        
    Returns:
        错误列表（空列表表示验证通过）
    """
    errors = []
    
    # 必需字段
    required_fields = ['slug', 'name', 'game', 'built_at', 'sources', 'kit', 'dimensions']
    
    for field in required_fields:
        if field not in manifest:
            errors.append(f"缺少必需字段：{field}")
    
    # 验证 slug 格式
    if 'slug' in manifest:
        if not re.match(r'^[a-z0-9-]+$', manifest['slug']):
            errors.append(f"slug 格式错误：{manifest['slug']}（应为小写字母、数字、连字符）")
    
    # 验证 dimensions
    if 'dimensions' in manifest:
        expected_dimensions = ['profile', 'personality', 'interaction', 'memory', 'relations']
        for dim in expected_dimensions:
            if dim not in manifest['dimensions']:
                errors.append(f"缺少维度：{dim}")
    
    # 验证 sources 格式
    if 'sources' in manifest:
        if not isinstance(manifest['sources'], list):
            errors.append("sources 应为列表")
    
    # 验证 built_at 格式（ISO 8601）
    if 'built_at' in manifest:
        try:
            datetime.fromisoformat(manifest['built_at'].replace('Z', '+00:00'))
        except:
            errors.append(f"built_at 格式错误：{manifest['built_at']}（应为 ISO 8601 格式）")
    
    return errors


def generate_manifest(
    name: str,
    game: str,
    sources: List[str],
    version: Optional[str] = None,
    evidence_summary: Optional[Dict] = None,
    quality_score: Optional[Dict] = None,
    test_results: Optional[Dict] = None
) -> Dict:
    """
    生成 manifest.json 内容
    
    Args:
        name: 角色名
        game: 游戏名
        sources: 数据来源列表
        version: 游戏版本（可选）
        evidence_summary: 证据统计（可选）
        quality_score: 质量评分（可选）
        test_results: 测试结果（可选）
        
    Returns:
        manifest 字典
    """
    now = datetime.now().isoformat()
    
    manifest = {
        'slug': to_slug(name),
        'name': name,
        'game': game,
        'built_at': now,
        'sources': sources,
        'kit': 'character-skill',
        'dimensions': ['profile', 'personality', 'interaction', 'memory', 'relations']
    }
    
    # 添加可选字段
    if version:
        manifest['source_version'] = version
        manifest['last_updated'] = now
    
    if evidence_summary:
        manifest['evidence_summary'] = evidence_summary
    
    if quality_score:
        manifest['quality_score'] = quality_score
    
    if test_results:
        manifest['test_results'] = test_results
    
    # 验证生成的 manifest
    errors = validate_manifest(manifest)
    if errors:
        print("警告：生成的 manifest 存在问题：")
        for error in errors:
            print(f"  - {error}")
    
    return manifest


def update_manifest(manifest_path: Path, updates: Dict) -> Dict:
    """
    更新现有 manifest.json
    
    Args:
        manifest_path: manifest.json 文件路径
        updates: 要更新的字段
        
    Returns:
        更新后的 manifest
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json 不存在：{manifest_path}")
    
    # 读取现有内容
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 更新字段
    manifest.update(updates)
    
    # 更新时间戳
    manifest['last_updated'] = datetime.now().isoformat()
    
    # 验证
    errors = validate_manifest(manifest)
    if errors:
        print("警告：更新后的 manifest 存在问题：")
        for error in errors:
            print(f"  - {error}")
    
    return manifest


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='manifest.json 生成与验证脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 生成新的 manifest
    python scripts/generate_manifest.py --character 芙宁娜 --game "原神 Genshin Impact" --sources genshin-wiki,in-game-text
    
    # 验证 manifest
    python scripts/generate_manifest.py --validate characters/furina-demo/manifest.json
    
    # 更新 manifest
    python scripts/generate_manifest.py --update characters/furina-demo/manifest.json --version 4.2
        """
    )
    
    # 生成模式
    parser.add_argument('--character', type=str, help='角色名')
    parser.add_argument('--game', type=str, help='游戏名')
    parser.add_argument('--sources', type=str, help='数据来源（逗号分隔）')
    parser.add_argument('--version', type=str, help='游戏版本')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    # 验证模式
    parser.add_argument('--validate', type=str, help='验证指定的 manifest.json 文件')
    
    # 更新模式
    parser.add_argument('--update', type=str, help='要更新的 manifest.json 文件')
    
    args = parser.parse_args()
    
    # 验证模式
    if args.validate:
        manifest_path = Path(args.validate)
        
        if not manifest_path.exists():
            print(f"错误：文件不存在：{manifest_path}")
            return
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        errors = validate_manifest(manifest)
        
        if errors:
            print("验证失败：")
            for error in errors:
                print(f"  ❌ {error}")
        else:
            print("✅ 验证通过")
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
        
        return
    
    # 更新模式
    if args.update:
        manifest_path = Path(args.update)
        
        updates = {}
        if args.version:
            updates['source_version'] = args.version
        
        if not updates:
            print("错误：未指定要更新的字段")
            return
        
        manifest = update_manifest(manifest_path, updates)
        
        # 保存
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已更新：{manifest_path}")
        return
    
    # 生成模式
    if args.character and args.game and args.sources:
        sources = [s.strip() for s in args.sources.split(',')]
        
        manifest = generate_manifest(
            name=args.character,
            game=args.game,
            sources=sources,
            version=args.version
        )
        
        # 输出
        output_json = json.dumps(manifest, ensure_ascii=False, indent=2)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_json, encoding='utf-8')
            print(f"✅ 已保存到：{output_path}")
        else:
            print(output_json)
        
        return
    
    parser.print_help()


if __name__ == '__main__':
    main()
