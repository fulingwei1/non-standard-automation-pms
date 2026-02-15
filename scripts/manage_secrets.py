#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密钥管理CLI工具

用法:
  python scripts/manage_secrets.py generate
  python scripts/manage_secrets.py rotate
  python scripts/manage_secrets.py validate <key>
  python scripts/manage_secrets.py list
  python scripts/manage_secrets.py cleanup
  python scripts/manage_secrets.py info

示例:
  # 生成新密钥
  python scripts/manage_secrets.py generate
  
  # 轮转密钥（自动生成新密钥）
  python scripts/manage_secrets.py rotate
  
  # 轮转密钥（使用指定密钥）
  python scripts/manage_secrets.py rotate --key "your-new-key"
  
  # 验证密钥
  python scripts/manage_secrets.py validate "your-secret-key"
  
  # 列出所有密钥
  python scripts/manage_secrets.py list
  
  # 清理过期密钥
  python scripts/manage_secrets.py cleanup --days 30
  
  # 查看密钥信息
  python scripts/manage_secrets.py info
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
from app.core.secret_manager import SecretKeyManager


@click.group()
def cli():
    """密钥管理工具
    
    提供密钥生成、轮转、验证、列出等功能
    """
    pass


@cli.command()
@click.option('--length', '-l', default=32, help='密钥长度（字节数），默认32')
@click.option('--count', '-c', default=1, help='生成密钥数量，默认1')
def generate(length: int, count: int):
    """生成新密钥
    
    生成加密安全的随机密钥（Base64 URL-safe编码）
    """
    manager = SecretKeyManager()
    
    click.echo(f"\n🔑 生成 {count} 个密钥（长度: {length} 字节）\n")
    click.echo("=" * 70)
    
    for i in range(count):
        new_key = manager.generate_key(length)
        
        if count > 1:
            click.echo(f"\n密钥 #{i+1}:")
        
        click.echo(f"\n{new_key}")
        click.echo(f"\n长度: {len(new_key)} 字符")
        click.echo(f"有效: {'✅' if manager.validate_key(new_key) else '❌'}")
        
        if i == 0:
            click.echo("\n" + "=" * 70)
            click.echo("\n📝 添加到 .env 文件:")
            click.echo(f"\nSECRET_KEY={new_key}")
            
            click.echo("\n" + "=" * 70)
            click.echo("\n🐳 Docker Secrets 配置:")
            click.echo(f"\n1. 创建密钥文件: echo '{new_key}' > secrets/secret_key.txt")
            click.echo("2. 在 docker-compose.yml 中引用:")
            click.echo("   secrets:")
            click.echo("     secret_key:")
            click.echo("       file: ./secrets/secret_key.txt")
            click.echo("\n" + "=" * 70)


@cli.command()
@click.option('--key', '-k', default=None, help='指定新密钥（可选，不提供则自动生成）')
@click.option('--yes', '-y', is_flag=True, help='跳过确认提示')
def rotate(key: str, yes: bool):
    """轮转密钥
    
    将当前密钥移到旧密钥列表，设置新密钥
    """
    manager = SecretKeyManager()
    
    try:
        manager.load_keys_from_env()
    except ValueError as e:
        click.echo(f"\n❌ 加载密钥失败: {e}", err=True)
        click.echo("\n提示: 请先设置 SECRET_KEY 环境变量", err=True)
        sys.exit(1)
    
    # 显示当前状态
    click.echo("\n📊 当前密钥状态:")
    click.echo("=" * 70)
    info = manager.get_key_info()
    click.echo(f"当前密钥: {info['current_key_preview']}")
    click.echo(f"旧密钥数量: {info['old_keys_count']}")
    
    # 确认操作
    if not yes:
        click.echo("\n" + "=" * 70)
        click.echo("\n⚠️  密钥轮转将:")
        click.echo("  1. 将当前密钥移到旧密钥列表")
        click.echo("  2. 设置新密钥")
        click.echo("  3. 旧Token仍可验证（30天有效期）")
        click.echo("  4. 需要更新环境变量并重启应用")
        
        if not click.confirm('\n确认轮转密钥?'):
            click.echo("\n已取消")
            return
    
    # 执行轮转
    try:
        result = manager.rotate_key(key)
        
        click.echo("\n" + "=" * 70)
        click.echo("\n✅ 密钥轮转成功!")
        click.echo("=" * 70)
        click.echo(f"\n新密钥: {result['new_key']}")
        click.echo(f"旧密钥: {result['old_key'][:10]}...")
        click.echo(f"轮转时间: {result['rotation_date']}")
        click.echo(f"旧密钥数量: {result['old_keys_count']}")
        
        click.echo("\n" + "=" * 70)
        click.echo("\n📝 更新 .env 文件:")
        click.echo(f"\nSECRET_KEY={result['new_key']}")
        
        if result.get('old_key'):
            old_keys = [result['old_key']] + manager.old_keys[1:]
            click.echo(f"OLD_SECRET_KEYS={','.join(old_keys)}")
        
        click.echo("\n" + "=" * 70)
        click.echo("\n⚠️  重要提示:")
        click.echo("  1. 立即更新环境变量")
        click.echo("  2. 重启应用以使用新密钥")
        click.echo("  3. 旧Token将在30天后失效")
        click.echo("  4. 建议通知用户重新登录")
        click.echo("\n" + "=" * 70)
        
    except ValueError as e:
        click.echo(f"\n❌ 轮转失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('key')
@click.option('--min-length', default=32, help='最小长度要求，默认32')
def validate(key: str, min_length: int):
    """验证密钥
    
    检查密钥是否满足安全要求
    """
    manager = SecretKeyManager()
    
    click.echo(f"\n🔍 验证密钥...")
    click.echo("=" * 70)
    click.echo(f"\n密钥预览: {key[:10]}...")
    click.echo(f"长度: {len(key)} 字符")
    click.echo(f"最小要求: {min_length} 字符")
    
    is_valid = manager.validate_key(key, min_length)
    
    click.echo("\n" + "=" * 70)
    
    if is_valid:
        click.echo("\n✅ 密钥有效")
        click.echo("\n密钥满足以下要求:")
        click.echo(f"  ✓ 长度 ≥ {min_length} 字符")
        click.echo("  ✓ Base64 URL-safe 编码")
        click.echo("  ✓ 格式正确")
    else:
        click.echo("\n❌ 密钥无效")
        click.echo("\n可能的问题:")
        if len(key) < min_length:
            click.echo(f"  ✗ 长度不足（需要至少 {min_length} 字符）")
        click.echo("  ✗ Base64编码错误或格式不正确")
        click.echo("\n建议:")
        click.echo("  使用 'python scripts/manage_secrets.py generate' 生成新密钥")
    
    click.echo("\n" + "=" * 70)
    sys.exit(0 if is_valid else 1)


@cli.command()
@click.option('--show-keys', is_flag=True, help='显示完整密钥（危险！）')
def list(show_keys: bool):
    """列出所有密钥
    
    显示当前密钥和旧密钥的信息
    """
    manager = SecretKeyManager()
    
    try:
        manager.load_keys_from_env()
    except ValueError as e:
        click.echo(f"\n❌ 加载密钥失败: {e}", err=True)
        sys.exit(1)
    
    info = manager.get_key_info()
    
    click.echo("\n📋 密钥列表")
    click.echo("=" * 70)
    
    # 当前密钥
    click.echo("\n🔑 当前密钥:")
    if show_keys:
        click.echo(f"  {manager.current_key}")
    else:
        click.echo(f"  {info['current_key_preview']}")
    click.echo(f"  长度: {info['current_key_length']} 字符")
    
    # 轮转信息
    if info['rotation_date']:
        click.echo(f"  轮转时间: {info['rotation_date']}")
    
    # 旧密钥
    click.echo(f"\n📦 旧密钥数量: {info['old_keys_count']}")
    
    if manager.old_keys:
        for i, old_key in enumerate(manager.old_keys):
            if show_keys:
                click.echo(f"  {i+1}. {old_key}")
            else:
                click.echo(f"  {i+1}. {old_key[:10]}... (长度: {len(old_key)})")
    
    # 元数据
    if info['metadata']:
        click.echo("\n📊 元数据:")
        for key, value in info['metadata'].items():
            click.echo(f"  {key}: {value}")
    
    click.echo("\n" + "=" * 70)
    
    if not show_keys:
        click.echo("\n提示: 使用 --show-keys 显示完整密钥（危险！）")


@cli.command()
@click.option('--days', '-d', default=30, help='旧密钥保留期（天），默认30')
@click.option('--yes', '-y', is_flag=True, help='跳过确认提示')
def cleanup(days: int, yes: bool):
    """清理过期密钥
    
    删除超过保留期的旧密钥
    """
    manager = SecretKeyManager()
    
    try:
        manager.load_keys_from_env()
    except ValueError as e:
        click.echo(f"\n❌ 加载密钥失败: {e}", err=True)
        sys.exit(1)
    
    click.echo(f"\n🧹 清理过期密钥（保留期: {days}天）")
    click.echo("=" * 70)
    
    info = manager.get_key_info()
    click.echo(f"\n旧密钥数量: {info['old_keys_count']}")
    
    if info['old_keys_count'] == 0:
        click.echo("\n✅ 没有旧密钥需要清理")
        return
    
    if not yes:
        if not click.confirm('\n确认清理过期密钥?'):
            click.echo("\n已取消")
            return
    
    cleaned_count = manager.cleanup_expired_keys(days)
    
    if cleaned_count > 0:
        click.echo(f"\n✅ 已清理 {cleaned_count} 个过期密钥")
    else:
        click.echo("\n✅ 没有过期密钥需要清理")
    
    click.echo("\n" + "=" * 70)


@cli.command()
def info():
    """查看密钥信息
    
    显示密钥管理器的状态信息
    """
    manager = SecretKeyManager()
    
    try:
        manager.load_keys_from_env()
    except ValueError as e:
        click.echo(f"\n❌ 加载密钥失败: {e}", err=True)
        click.echo("\n提示: 请先设置 SECRET_KEY 环境变量", err=True)
        sys.exit(1)
    
    info = manager.get_key_info()
    
    click.echo("\n📊 密钥管理器信息")
    click.echo("=" * 70)
    
    click.echo("\n🔑 当前密钥:")
    click.echo(f"  预览: {info['current_key_preview']}")
    click.echo(f"  长度: {info['current_key_length']} 字符")
    click.echo(f"  有效: ✅")
    
    click.echo("\n📦 旧密钥:")
    click.echo(f"  数量: {info['old_keys_count']}")
    click.echo(f"  最大保留数量: 3")
    
    if info['rotation_date']:
        click.echo(f"\n🔄 最后轮转:")
        click.echo(f"  时间: {info['rotation_date']}")
    else:
        click.echo("\n🔄 轮转记录: 无")
    
    if info['metadata']:
        click.echo("\n📋 元数据:")
        for key, value in info['metadata'].items():
            click.echo(f"  {key}: {value}")
    
    click.echo("\n🔐 安全配置:")
    
    # 检查环境变量配置
    secret_key_file = os.getenv("SECRET_KEY_FILE")
    old_keys_file = os.getenv("OLD_SECRET_KEYS_FILE")
    
    if secret_key_file:
        exists = "✅" if os.path.exists(secret_key_file) else "❌"
        click.echo(f"  SECRET_KEY_FILE: {exists} {secret_key_file}")
    else:
        click.echo("  SECRET_KEY_FILE: ⚠️  未设置（使用环境变量）")
    
    if old_keys_file:
        exists = "✅" if os.path.exists(old_keys_file) else "❌"
        click.echo(f"  OLD_SECRET_KEYS_FILE: {exists} {old_keys_file}")
    else:
        click.echo("  OLD_SECRET_KEYS_FILE: 未设置")
    
    click.echo("\n" + "=" * 70)
    
    # 安全建议
    click.echo("\n💡 安全建议:")
    click.echo("  1. 定期轮转密钥（建议每90天）")
    click.echo("  2. 生产环境使用 Docker Secrets 或密钥管理服务")
    click.echo("  3. 永远不要在代码中硬编码密钥")
    click.echo("  4. 保持旧密钥列表在3个以内")
    click.echo("  5. 密钥轮转后通知用户重新登录")
    
    click.echo("\n" + "=" * 70)


if __name__ == '__main__':
    cli()
