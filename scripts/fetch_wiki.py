#!/usr/bin/env python3
"""
Wiki 内容获取脚本（重写版）

功能：
- 从多个 Wiki 源获取角色设定
- 支持：原神、崩坏星穹铁道、三角洲行动
- 三种获取模式：markdown 服务、异步 HTTP、同步降级
- 支持批量异步获取
- 自动清理 Markdown 内容

依赖：
- httpx>=0.27.0（可选，用于异步模式）
- selectolax>=0.3.21（可选，用于 HTML 解析）

用法：
    python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜
    python scripts/fetch_wiki.py --game genshin --wiki moegirl --characters 芙宁娜,钟离,胡桃(原神) --concurrency 5
"""

import argparse
import asyncio
import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

# 尝试导入可选依赖
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from selectolax.parser import HTMLParser
    HAS_SELECTOLAX = True
except ImportError:
    HAS_SELECTOLAX = False


# Wiki 配置
WIKI_CONFIGS = {
    'genshin': {
        'name': '原神',
        'wikis': {
            'moegirl': {
                'name': '萌娘百科',
                'url_template': 'https://mzh.moegirl.org.cn/{name}',
            },
            'bwiki': {
                'name': 'BWIKI',
                'url_template': 'https://wiki.biligame.com/ys/{name}',
            },
            'fandom': {
                'name': 'Fandom',
                'url_template': 'https://genshin-impact.fandom.com/wiki/{name}',
            }
        }
    },
    'hsr': {
        'name': '崩坏：星穹铁道',
        'wikis': {
            'moegirl': {
                'name': '萌娘百科',
                'url_template': 'https://mzh.moegirl.org.cn/{name}',
            },
            'bwiki': {
                'name': 'BWIKI',
                'url_template': 'https://wiki.biligame.com/sr/{name}',
            },
            'fandom': {
                'name': 'Fandom',
                'url_template': 'https://honkai-star-rail.fandom.com/wiki/{name}',
            }
        }
    },
    'deltaforce': {
        'name': '三角洲行动',
        'wikis': {
            'bwiki': {
                'name': 'BWIKI',
                'url_template': 'https://wiki.biligame.com/deltaforce/{name}',
            },
            'moegirl': {
                'name': '萌娘百科',
                'url_template': 'https://mzh.moegirl.org.cn/{name}',
            }
        }
    }
}

# Markdown 服务配置
MARKDOWN_SERVICE = {
    'name': 'markdown.new',
    'prefix': 'https://markdown.new/',
}


# ============== Markdown 清理 ==============

def load_cleanup_rules() -> Dict:
    """加载清理规则"""
    rules_path = Path(__file__).parent / 'cleanup_rules.json'
    
    if rules_path.exists():
        with open(rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认规则
    return {
        'moegirl': {
            'remove_patterns': [
                '✦向着星辰与深渊✦',
                '欢迎正在阅读这个条目的旅行者协助编辑本条目',
                '编辑前请阅读提瓦特游览指南或骑士团指导手册·第五版',
            ]
        },
        'bwiki': {
            'remove_patterns': []
        },
        'fandom': {
            'remove_patterns': []
        }
    }


def extract_english_name(content: str) -> Optional[str]:
    """
    从 Wiki 内容中提取英文名
    
    Args:
        content: Markdown 内容
        
    Returns:
        英文名（如果找到）
    """
    # 匹配 "英：Name" 格式
    match = re.search(r'英[：:]\s*([^\n]+)', content)
    if match:
        name = match.group(1).strip()
        # 只取第一个单词作为目录名（如 "Columbina Hyposelenia" -> "columbina"）
        first_name = name.split()[0] if name.split() else name
        return first_name.lower()
    return None


def clean_markdown(content: str, wiki_type: str) -> tuple:
    """
    清理 Markdown 内容
    
    Args:
        content: 原始 Markdown 内容
        wiki_type: Wiki 类型
        
    Returns:
        (清理后的 Markdown 内容, 英文名)
    """
    # 0. 提取英文名（在清理之前）
    english_name = extract_english_name(content)
    
    # 1. 移除 frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    # 2. 针对萌娘百科的深度清理
    if wiki_type == 'moegirl':
        # 2.1 删除开头"基本资料"之前的内容
        lines = content.split('\n')
        basic_info_index = -1
        for i, line in enumerate(lines):
            if line.strip() == '基本资料':
                basic_info_index = i
                break
        
        if basic_info_index > 0:
            content = '\n'.join(lines[basic_info_index:])
        
        # 2.2 删除导航模板
        # 匹配 | [查] 或 | 「查」 开头的导航表格
        content = re.sub(
            r'\|\s*(?:\[查\]|「查」).*?(?=##\s*(?:注释|外部链接)|$)',
            '',
            content,
            flags=re.DOTALL
        )
        
        # 2.3 删除结尾的 JSON-LD 代码块
        content = re.sub(r'\n```json\n.*?\n```\s*$', '', content, flags=re.DOTALL)
    
    # 3. 转换内部链接为纯文本格式（所有Wiki源）
    # 只转换以 / 开头的内部链接，保留脚注引用和外部链接
    content = re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: f'「{m.group(1)}」' if m.group(2).startswith('/') else m.group(0),
        content
    )
    
    # 4. 移除空链接
    content = re.sub(r'\[\]\([^)]+\)', '', content)
    
    # 5. 移除视频引用
    content = re.sub(r'宽屏模式显示视频', '', content)
    
    # 6. 移除 Lorem ipsum 占位符表格
    content = re.sub(
        r'\|\s*Lorem ipsum[^|]*\|\s*\n\|[-\s|]+\|',
        '',
        content,
        flags=re.IGNORECASE
    )
    
    # 7. 移除技能倍率表格（萌娘百科特有）
    # 匹配两种格式：
    # 1. 多行表格：| 详细属性 | Lv.1 | ... | \n |---|...|\n 数据行...
    # 2. 单行表格：| 详细属性 Lv.1 ... 一段伤害 48.4% ... |
    if wiki_type == 'moegirl':
        # 删除多行表格
        content = re.sub(
            r'\|\s*详细属性\s*\|[^|]*Lv\.[^\n]*\n'  # 表头行
            r'\|[-\s|]+\n'  # 分隔符行
            r'(?:\|[^|]*\|[^\n]*\n)*'  # 数据行（多行）
            r'(?=\n)',  # 空行结束
            '',
            content,
            flags=re.MULTILINE
        )
        
        # 删除单行表格（芙宁娜格式）
        content = re.sub(
            r'\|\s*详细属性\s+Lv\.[^|]*\|',
            '',
            content,
            flags=re.IGNORECASE
        )
    
    # 8. 加载特定规则
    rules = load_cleanup_rules()
    
    if wiki_type in rules:
        for pattern in rules[wiki_type].get('remove_patterns', []):
            content = content.replace(pattern, '')
    
    # 7. 移除多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip(), english_name


# ============== 获取方法 ==============

def fetch_via_markdown_service(url: str, timeout: int = 30) -> Optional[str]:
    """
    通过 markdown.new 服务获取内容
    
    Args:
        url: 原始 URL
        timeout: 超时时间
        
    Returns:
        Markdown 内容
    """
    try:
        markdown_url = f"{MARKDOWN_SERVICE['prefix']}{url.replace('https://', '').replace('http://', '')}"
        
        print(f"  尝试 Markdown 服务：{markdown_url}")
        
        req = urllib.request.Request(
            markdown_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8')
            return content
    
    except Exception as e:
        print(f"  Markdown 服务失败：{e}")
        return None


async def fetch_via_httpx_async(url: str, timeout: int = 30) -> Optional[str]:
    """
    使用 httpx 异步获取
    
    Args:
        url: URL
        timeout: 超时时间
        
    Returns:
        HTML 内容
    """
    if not HAS_HTTPX:
        return None
    
    try:
        print(f"  尝试 httpx 异步获取：{url}")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            response.raise_for_status()
            return response.text
    
    except Exception as e:
        print(f"  httpx 获取失败：{e}")
        return None


def fetch_via_urllib(url: str, timeout: int = 30) -> Optional[str]:
    """
    使用 urllib 同步获取（降级方案）
    
    Args:
        url: URL
        timeout: 超时时间
        
    Returns:
        HTML 内容
    """
    try:
        print(f"  尝试 urllib 同步获取：{url}")
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read().decode('utf-8')
            return content
    
    except Exception as e:
        print(f"  urllib 获取失败：{e}")
        return None


def parse_html_to_markdown(html: str) -> str:
    """
    解析 HTML 为 Markdown
    
    Args:
        html: HTML 内容
        
    Returns:
        Markdown 内容
    """
    if HAS_SELECTOLAX:
        # 使用 selectolax 解析
        parser = HTMLParser(html)
        
        # 移除脚本和样式
        for tag in parser.css('script, style, nav, footer'):
            tag.decompose()
        
        # 提取正文
        content_div = parser.css_first('div.mw-parser-output')
        if content_div:
            text = content_div.text(separator='\n')
        else:
            text = parser.text(separator='\n')
        
        return text
    
    else:
        # 使用正则提取（降级）
        # 移除 script 和 style 标签
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # 移除所有 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()


# ============== 主要函数 ==============

def fetch_wiki_content(
    character: str,
    game: str,
    wiki: str,
    method: str = 'auto',
    timeout: int = 30
) -> Dict:
    """
    获取 Wiki 内容（混合策略）
    
    Args:
        character: 角色名
        game: 游戏标识
        wiki: Wiki 标识
        method: 获取方法（auto/markdown/httpx/urllib）
        timeout: 超时时间
        
    Returns:
        结果字典
    """
    # 检查配置
    if game not in WIKI_CONFIGS:
        return {'success': False, 'error': f'不支持的游戏：{game}'}
    
    if wiki not in WIKI_CONFIGS[game]['wikis']:
        return {'success': False, 'error': f'不支持的 Wiki：{wiki}'}
    
    # 构建 URL
    wiki_config = WIKI_CONFIGS[game]['wikis'][wiki]
    url = wiki_config['url_template'].format(name=quote(character))
    
    print(f"\n获取角色：{character}")
    print(f"  URL：{url}")
    
    content = None
    used_method = None
    
    # 根据方法选择获取方式
    if method == 'markdown':
        content = fetch_via_markdown_service(url, timeout)
        used_method = 'markdown'
    
    elif method == 'httpx':
        if HAS_HTTPX:
            # 同步调用异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                html = loop.run_until_complete(fetch_via_httpx_async(url, timeout))
                if html:
                    content = parse_html_to_markdown(html)
                used_method = 'httpx'
            finally:
                loop.close()
        else:
            return {'success': False, 'error': 'httpx 未安装'}
    
    elif method == 'urllib':
        html = fetch_via_urllib(url, timeout)
        if html:
            content = parse_html_to_markdown(html)
        used_method = 'urllib'
    
    elif method == 'auto':
        # 自动选择：markdown -> httpx -> urllib
        content = fetch_via_markdown_service(url, timeout)
        if content:
            used_method = 'markdown'
        else:
            if HAS_HTTPX:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    html = loop.run_until_complete(fetch_via_httpx_async(url, timeout))
                    if html:
                        content = parse_html_to_markdown(html)
                    used_method = 'httpx'
                finally:
                    loop.close()
            
            if not content:
                html = fetch_via_urllib(url, timeout)
                if html:
                    content = parse_html_to_markdown(html)
                used_method = 'urllib'
    
    else:
        return {'success': False, 'error': f'未知的获取方法：{method}'}
    
    if not content:
        return {'success': False, 'error': '所有获取方法均失败'}
    
    # 清理内容
    print(f"  清理内容...")
    content, english_name = clean_markdown(content, wiki)
    
    return {
        'success': True,
        'character': character,
        'english_name': english_name,
        'url': url,
        'wiki_name': wiki_config['name'],
        'game_name': WIKI_CONFIGS[game]['name'],
        'content': content,
        'content_length': len(content),
        'used_method': used_method
    }


async def fetch_multiple_wiki_async(
    characters: List[str],
    game: str,
    wiki: str,
    concurrency: int = 5,
    timeout: int = 30,
    output_dir: Path = None
) -> Dict:
    """
    批量异步获取多个角色
    
    Args:
        characters: 角色列表
        game: 游戏标识
        wiki: Wiki 标识
        concurrency: 并发数
        timeout: 超时时间
        output_dir: 输出目录
        
    Returns:
        汇总结果
    """
    if concurrency > 10:
        print(f"警告：并发数 {concurrency} 过大，已限制为 10")
        concurrency = 10
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def fetch_one(character: str) -> Dict:
        async with semaphore:
            # 在异步环境中调用同步函数
            result = fetch_wiki_content(character, game, wiki, 'auto', timeout)
            
            # 保存文件
            if result['success'] and output_dir:
                output_path = output_dir / character / 'sources' / 'wiki.md'
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                header = f"""# {character}

> 来源：{result['wiki_name']}
> 游戏：{result['game_name']}
> URL：{result['url']}
> 获取时间：{__import__('datetime').datetime.now().isoformat()}
> 获取方式：{result['used_method']}

---

"""
                output_path.write_text(header + result['content'], encoding='utf-8')
                result['output_path'] = str(output_path)
            
            return result
    
    print(f"\n批量获取 {len(characters)} 个角色（并发数：{concurrency}）")
    print("="*60)
    
    tasks = [fetch_one(char) for char in characters]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(1 for r in results if r['success'])
    
    print("\n" + "="*60)
    print(f"完成！成功：{success_count}/{len(characters)}")
    
    return {
        'total': len(characters),
        'success': success_count,
        'failed': len(characters) - success_count,
        'results': results
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Wiki 内容获取脚本（支持三种模式）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的游戏：
  - genshin     原神
  - hsr         崩坏：星穹铁道
  - deltaforce  三角洲行动

支持的 Wiki：
  - moegirl     萌娘百科（中文首选）
  - bwiki       BWIKI（中文补充）
  - fandom      Fandom（英文首选）

获取方式：
  - auto        自动选择（默认）：markdown → httpx → urllib
  - markdown    强制使用 markdown.new 服务
  - httpx       强制使用 httpx 异步获取
  - urllib      强制使用 urllib 同步获取

示例：
    # 获取单个角色
    python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜
    
    # 批量获取
    python scripts/fetch_wiki.py --game genshin --wiki moegirl \\
        --characters 芙宁娜,钟离,胡桃(原神) --concurrency 5
    
    # 从文件读取角色列表
    python scripts/fetch_wiki.py --game genshin --wiki moegirl \\
        --input characters.txt --concurrency 10
    
    # 指定获取方式
    python scripts/fetch_wiki.py --game genshin --wiki moegirl --character 芙宁娜 --method markdown
        """
    )
    
    parser.add_argument('--game', required=True, help='游戏标识')
    parser.add_argument('--wiki', required=True, help='Wiki 标识')
    parser.add_argument('--character', help='角色名')
    parser.add_argument('--characters', help='角色列表（逗号分隔）')
    parser.add_argument('--input', help='角色列表文件')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--output-dir', help='批量输出目录')
    parser.add_argument('--method', default='auto', choices=['auto', 'markdown', 'httpx', 'urllib'],
                        help='获取方式（默认 auto）')
    parser.add_argument('--concurrency', type=int, default=5, help='并发数（默认 5，最大 10）')
    parser.add_argument('--timeout', type=int, default=30, help='超时时间（秒，默认 30）')
    parser.add_argument('--no-cleanup', action='store_true', help='不清理内容')
    
    args = parser.parse_args()
    
    # 读取角色列表
    characters = []
    
    if args.character:
        characters = [args.character]
    elif args.characters:
        characters = [c.strip() for c in args.characters.split(',')]
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"错误：文件不存在：{input_path}")
            return
        characters = [line.strip() for line in input_path.read_text().splitlines() if line.strip()]
    else:
        parser.print_help()
        return
    
    if not characters:
        print("错误：未指定任何角色")
        return
    
    # 批量获取
    if len(characters) > 1:
        output_dir = Path(args.output_dir) if args.output_dir else Path('raw')
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                fetch_multiple_wiki_async(
                    characters, args.game, args.wiki,
                    args.concurrency, args.timeout, output_dir
                )
            )
            
            # 输出汇总
            for r in result['results']:
                if r['success']:
                    print(f"  ✅ {r['character']}: {r['content_length']} 字符 ({r['used_method']})")
                else:
                    print(f"  ❌ {r['character']}: {r['error']}")
        
        finally:
            loop.close()
    
    # 单个获取
    else:
        result = fetch_wiki_content(characters[0], args.game, args.wiki, args.method, args.timeout)
        
        if result['success']:
            print(f"\n✅ 获取成功")
            print(f"   Wiki：{result['wiki_name']}")
            print(f"   方式：{result['used_method']}")
            print(f"   长度：{result['content_length']} 字符")
            if result.get('english_name'):
                print(f"   英文名：{result['english_name']}")
            
            # 保存
            if args.output:
                output_path = Path(args.output)
            elif result.get('english_name'):
                # 使用英文名自动创建目录
                output_path = Path('characters') / result['english_name'] / 'sources' / 'wiki.md'
            else:
                output_path = None
            
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                header = f"""# {result['character']}

> 来源：{result['wiki_name']}
> 游戏：{result['game_name']}
> URL：{result['url']}
> 获取时间：{__import__('datetime').datetime.now().isoformat()}
> 获取方式：{result['used_method']}

---

"""
                output_path.write_text(header + result['content'], encoding='utf-8')
                print(f"   已保存：{output_path}")
            
            elif not args.no_cleanup:
                # 显示部分内容
                preview = result['content'][:500]
                print(f"\n预览：\n{preview}...")
        else:
            print(f"\n❌ 获取失败：{result['error']}")


if __name__ == '__main__':
    main()
