#!/usr/bin/env python3
"""
文件管理脚本

功能：
- 创建角色目录结构
- 备份版本
- 回滚到指定版本
- 列出所有版本

用法：
    python scripts/file_manager.py --create <角色名>
    python scripts/file_manager.py --backup <角色名> --version <版本号>
    python scripts/file_manager.py --rollback <角色名> --version <版本号>
    python scripts/file_manager.py --list <角色名>
"""

import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional


# 维度文件列表
DIMENSION_FILES = [
    'SKILL.md',
    'profile.md',
    'personality.md',
    'interaction.md',
    'memory.md',
    'relations.md',
    'conflicts.md',
    'manifest.json'
]


def create_character_structure(slug: str, base_dir: Path = None) -> Path:
    """
    创建角色目录结构
    
    Args:
        slug: 角色标识（小写字母、数字、连字符）
        base_dir: 基础目录（默认为 characters/）
        
    Returns:
        角色目录路径
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    # 创建目录
    character_dir = base_dir / slug
    character_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建版本目录
    versions_dir = character_dir / 'versions'
    versions_dir.mkdir(exist_ok=True)
    
    # 创建模板文件
    for file_name in DIMENSION_FILES:
        file_path = character_dir / file_name
        if not file_path.exists():
            file_path.touch()
    
    print(f"✅ 已创建角色目录：{character_dir}")
    
    return character_dir


def backup_version(slug: str, version: str, base_dir: Path = None) -> Path:
    """
    备份当前版本
    
    Args:
        slug: 角色标识
        version: 版本号
        base_dir: 基础目录
        
    Returns:
        备份目录路径
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    character_dir = base_dir / slug
    versions_dir = character_dir / 'versions'
    
    if not character_dir.exists():
        raise FileNotFoundError(f"角色目录不存在：{character_dir}")
    
    # 创建备份目录
    version_dir = versions_dir / version
    if version_dir.exists():
        print(f"警告：版本 {version} 已存在，将被覆盖")
        shutil.rmtree(version_dir)
    
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制文件
    for file_name in DIMENSION_FILES:
        src = character_dir / file_name
        dst = version_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
    
    print(f"✅ 已备份版本 {version} 到：{version_dir}")
    
    return version_dir


def rollback_version(slug: str, version: str, base_dir: Path = None) -> None:
    """
    回滚到指定版本
    
    Args:
        slug: 角色标识
        version: 版本号
        base_dir: 基础目录
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    character_dir = base_dir / slug
    versions_dir = character_dir / 'versions'
    version_dir = versions_dir / version
    
    if not version_dir.exists():
        raise FileNotFoundError(f"版本 {version} 不存在：{version_dir}")
    
    # 备份当前版本（以防万一）
    print("正在备份当前版本...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_version(slug, f"pre_rollback_{timestamp}", base_dir)
    
    # 恢复文件
    for file_name in DIMENSION_FILES:
        src = version_dir / file_name
        dst = character_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
    
    print(f"✅ 已回滚到版本 {version}")


def list_versions(slug: str, base_dir: Path = None) -> List[str]:
    """
    列出所有版本
    
    Args:
        slug: 角色标识
        base_dir: 基础目录
        
    Returns:
        版本列表
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    character_dir = base_dir / slug
    versions_dir = character_dir / 'versions'
    
    if not versions_dir.exists():
        return []
    
    versions = [d.name for d in versions_dir.iterdir() if d.is_dir()]
    versions.sort()
    
    return versions


def delete_version(slug: str, version: str, base_dir: Path = None) -> None:
    """
    删除指定版本
    
    Args:
        slug: 角色标识
        version: 版本号
        base_dir: 基础目录
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    character_dir = base_dir / slug
    versions_dir = character_dir / 'versions'
    version_dir = versions_dir / version
    
    if not version_dir.exists():
        raise FileNotFoundError(f"版本 {version} 不存在：{version_dir}")
    
    shutil.rmtree(version_dir)
    print(f"✅ 已删除版本 {version}")


def clean_old_versions(slug: str, keep: int = 3, base_dir: Path = None) -> List[str]:
    """
    清理旧版本，只保留最近的 N 个版本
    
    Args:
        slug: 角色标识
        keep: 保留的版本数量
        base_dir: 基础目录
        
    Returns:
        被删除的版本列表
    """
    if base_dir is None:
        base_dir = Path('characters')
    
    versions = list_versions(slug, base_dir)
    
    if len(versions) <= keep:
        print(f"当前版本数：{len(versions)}，无需清理")
        return []
    
    # 删除旧版本
    to_delete = versions[:-keep]
    deleted = []
    
    for version in to_delete:
        try:
            delete_version(slug, version, base_dir)
            deleted.append(version)
        except Exception as e:
            print(f"删除版本 {version} 失败：{e}")
    
    print(f"✅ 已清理 {len(deleted)} 个旧版本")
    
    return deleted


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='文件管理脚本 - 创建、备份、回滚角色版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 创建角色目录
    python scripts/file_manager.py --create furina-demo
    
    # 备份当前版本
    python scripts/file_manager.py --backup furina-demo --version 4.2
    
    # 列出所有版本
    python scripts/file_manager.py --list furina-demo
    
    # 回滚到指定版本
    python scripts/file_manager.py --rollback furina-demo --version 4.1
    
    # 清理旧版本（保留最近3个）
    python scripts/file_manager.py --clean furina-demo --keep 3
        """
    )
    
    parser.add_argument('--create', type=str, help='创建角色目录')
    parser.add_argument('--backup', type=str, help='备份当前版本')
    parser.add_argument('--rollback', type=str, help='回滚到指定版本')
    parser.add_argument('--list', type=str, help='列出所有版本')
    parser.add_argument('--delete', type=str, help='删除指定版本')
    parser.add_argument('--clean', type=str, help='清理旧版本')
    
    parser.add_argument('--version', type=str, help='版本号')
    parser.add_argument('--keep', type=int, default=3, help='保留的版本数量（默认3）')
    parser.add_argument('--base-dir', type=str, help='基础目录')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir) if args.base_dir else None
    
    # 创建目录
    if args.create:
        create_character_structure(args.create, base_dir)
        return
    
    # 备份版本
    if args.backup:
        if not args.version:
            print("错误：未指定版本号（--version）")
            return
        backup_version(args.backup, args.version, base_dir)
        return
    
    # 列出版本
    if args.list:
        versions = list_versions(args.list, base_dir)
        if versions:
            print(f"版本列表：")
            for v in versions:
                print(f"  - {v}")
        else:
            print("暂无版本")
        return
    
    # 回滚版本
    if args.rollback:
        if not args.version:
            print("错误：未指定版本号（--version）")
            return
        rollback_version(args.rollback, args.version, base_dir)
        return
    
    # 删除版本
    if args.delete:
        if not args.version:
            print("错误：未指定版本号（--version）")
            return
        delete_version(args.delete, args.version, base_dir)
        return
    
    # 清理旧版本
    if args.clean:
        clean_old_versions(args.clean, args.keep, base_dir)
        return
    
    parser.print_help()


if __name__ == '__main__':
    main()
