#!/usr/bin/env python3
"""
数据加密密钥生成工具

用法:
  python scripts/generate_encryption_key.py
  python scripts/generate_encryption_key.py --save
"""

import os
import sys
import click

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.encryption import DataEncryption


@click.command()
@click.option('--save', is_flag=True, help='保存到 .env 文件（需要手动添加到环境变量）')
@click.option('--output', default='.env.encryption', help='输出文件路径（默认：.env.encryption）')
def generate_key(save: bool, output: str):
    """
    生成数据加密密钥
    
    Args:
        save: 是否保存到文件
        output: 输出文件路径
    """
    click.echo("\n" + "="*60)
    click.echo("🔑 数据加密密钥生成工具")
    click.echo("="*60)
    
    # 生成密钥
    key = DataEncryption.generate_key()
    
    click.echo("\n✅ 加密密钥已生成：")
    click.echo("\n" + "-"*60)
    click.echo(f"DATA_ENCRYPTION_KEY={key}")
    click.echo("-"*60)
    
    # 保存到文件
    if save:
        try:
            with open(output, 'w') as f:
                f.write(f"# 数据加密密钥（请妥善保管）\n")
                f.write(f"# 生成时间: {os.popen('date').read().strip()}\n")
                f.write(f"DATA_ENCRYPTION_KEY={key}\n")
            
            click.echo(f"\n✅ 密钥已保存到文件: {output}")
            click.echo(f"\n⚠️  请将以下内容添加到 .env 文件：")
            click.echo(f"   cp {output} .env  # 或手动复制")
        except Exception as e:
            click.echo(f"\n❌ 保存失败: {e}")
    
    # 使用说明
    click.echo("\n" + "="*60)
    click.echo("📖 使用说明")
    click.echo("="*60)
    click.echo("\n1. 将密钥添加到 .env 文件：")
    click.echo(f"   echo 'DATA_ENCRYPTION_KEY={key}' >> .env")
    
    click.echo("\n2. 或者设置为环境变量：")
    click.echo(f"   export DATA_ENCRYPTION_KEY={key}")
    
    click.echo("\n3. 重启应用：")
    click.echo("   ./stop.sh && ./start.sh")
    
    click.echo("\n⚠️  安全提示：")
    click.echo("   - 密钥一旦丢失，已加密数据将无法解密！")
    click.echo("   - 请妥善保管密钥，不要提交到 Git 仓库")
    click.echo("   - 生产环境建议使用密钥管理服务（如 AWS KMS）")
    click.echo("   - 定期备份密钥到安全位置")
    
    click.echo("\n" + "="*60 + "\n")


@click.command()
@click.option('--key', required=True, help='要验证的密钥')
def verify_key(key: str):
    """
    验证密钥格式是否正确
    
    Args:
        key: 要验证的密钥
    """
    import base64
    
    click.echo("\n" + "="*60)
    click.echo("🔍 密钥格式验证")
    click.echo("="*60)
    
    try:
        # 尝试解码
        decoded = base64.urlsafe_b64decode(key)
        
        # 检查长度（256位 = 32字节）
        if len(decoded) == 32:
            click.echo("\n✅ 密钥格式正确！")
            click.echo(f"   长度: {len(decoded)} 字节 (256位)")
        else:
            click.echo(f"\n❌ 密钥长度错误！")
            click.echo(f"   当前: {len(decoded)} 字节")
            click.echo(f"   期望: 32 字节 (256位)")
    
    except Exception as e:
        click.echo(f"\n❌ 密钥格式错误: {e}")
    
    click.echo("\n" + "="*60 + "\n")


@click.group()
def cli():
    """数据加密密钥管理工具"""
    pass


cli.add_command(generate_key, name='generate')
cli.add_command(verify_key, name='verify')


if __name__ == '__main__':
    # 如果没有参数，默认执行 generate
    if len(sys.argv) == 1:
        generate_key()
    else:
        cli()
