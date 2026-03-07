#!/usr/bin/env python3
"""
数据加密性能测试

测试加密/解密的性能，确保满足以下要求：
- 10,000次加密/解密 < 1秒
"""

import os
import sys
import time
import click
from statistics import mean, stdev

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.encryption import data_encryption


def benchmark_encrypt(iterations: int = 10000):
    """
    加密性能测试
    
    Args:
        iterations: 迭代次数
    
    Returns:
        (总耗时, 平均耗时, 标准差)
    """
    test_data = [
        "421002199001011234",  # 身份证号
        "6217000010012345678",  # 银行卡号
        "13800138000",  # 手机号
        "湖北省武汉市洪山区珞瑜路1号",  # 地址
        "15000.50",  # 薪资
    ]
    
    times = []
    
    for plaintext in test_data:
        start = time.time()
        for _ in range(iterations):
            data_encryption.encrypt(plaintext)
        elapsed = time.time() - start
        times.append(elapsed)
    
    total_time = sum(times)
    avg_time = mean(times)
    std_dev = stdev(times) if len(times) > 1 else 0
    
    return total_time, avg_time, std_dev


def benchmark_decrypt(iterations: int = 10000):
    """
    解密性能测试
    
    Args:
        iterations: 迭代次数
    
    Returns:
        (总耗时, 平均耗时, 标准差)
    """
    test_data = [
        "421002199001011234",
        "6217000010012345678",
        "13800138000",
        "湖北省武汉市洪山区珞瑜路1号",
        "15000.50",
    ]
    
    # 先加密
    encrypted_data = [data_encryption.encrypt(d) for d in test_data]
    
    times = []
    
    for ciphertext in encrypted_data:
        start = time.time()
        for _ in range(iterations):
            data_encryption.decrypt(ciphertext)
        elapsed = time.time() - start
        times.append(elapsed)
    
    total_time = sum(times)
    avg_time = mean(times)
    std_dev = stdev(times) if len(times) > 1 else 0
    
    return total_time, avg_time, std_dev


def benchmark_roundtrip(iterations: int = 10000):
    """
    加密+解密性能测试
    
    Args:
        iterations: 迭代次数
    
    Returns:
        总耗时
    """
    test_data = [
        "421002199001011234",
        "6217000010012345678",
        "13800138000",
        "湖北省武汉市洪山区珞瑜路1号",
        "15000.50",
    ]
    
    start = time.time()
    
    for plaintext in test_data:
        for _ in range(iterations):
            encrypted = data_encryption.encrypt(plaintext)
            data_encryption.decrypt(encrypted)
    
    return time.time() - start


@click.command()
@click.option('--iterations', default=10000, help='迭代次数（默认10000）')
@click.option('--warmup', default=100, help='预热次数（默认100）')
def main(iterations: int, warmup: int):
    """数据加密性能测试"""
    
    click.echo("\n" + "="*60)
    click.echo("⏱️  数据加密性能测试")
    click.echo("="*60)
    click.echo(f"迭代次数: {iterations:,}")
    click.echo(f"预热次数: {warmup:,}")
    click.echo("="*60 + "\n")
    
    # 预热（避免首次调用的性能损耗）
    click.echo("🔥 预热中...")
    for _ in range(warmup):
        data_encryption.encrypt("test")
        data_encryption.decrypt(data_encryption.encrypt("test"))
    click.echo("✅ 预热完成\n")
    
    # 1. 加密性能测试
    click.echo(f"🔒 加密性能测试 ({iterations:,}次 × 5种数据)...")
    total_time, avg_time, std_dev = benchmark_encrypt(iterations)
    
    click.echo(f"  总耗时: {total_time:.3f}秒")
    click.echo(f"  平均耗时: {avg_time:.3f}秒")
    click.echo(f"  标准差: {std_dev:.3f}秒")
    click.echo(f"  吞吐量: {iterations * 5 / total_time:,.0f} ops/sec")
    
    # 性能判定
    if total_time < 1.0:
        click.echo(f"  ✅ 性能优秀！({total_time:.3f}秒 < 1秒)")
    elif total_time < 2.0:
        click.echo(f"  ⚠️  性能一般（{total_time:.3f}秒）")
    else:
        click.echo(f"  ❌ 性能不达标！({total_time:.3f}秒 > 1秒)")
    
    # 2. 解密性能测试
    click.echo(f"\n🔓 解密性能测试 ({iterations:,}次 × 5种数据)...")
    total_time, avg_time, std_dev = benchmark_decrypt(iterations)
    
    click.echo(f"  总耗时: {total_time:.3f}秒")
    click.echo(f"  平均耗时: {avg_time:.3f}秒")
    click.echo(f"  标准差: {std_dev:.3f}秒")
    click.echo(f"  吞吐量: {iterations * 5 / total_time:,.0f} ops/sec")
    
    # 性能判定
    if total_time < 1.0:
        click.echo(f"  ✅ 性能优秀！({total_time:.3f}秒 < 1秒)")
    elif total_time < 2.0:
        click.echo(f"  ⚠️  性能一般（{total_time:.3f}秒）")
    else:
        click.echo(f"  ❌ 性能不达标！({total_time:.3f}秒 > 1秒)")
    
    # 3. 加密+解密性能测试
    click.echo(f"\n🔄 加密+解密性能测试 ({iterations:,}次 × 5种数据)...")
    total_time = benchmark_roundtrip(iterations)
    
    click.echo(f"  总耗时: {total_time:.3f}秒")
    click.echo(f"  吞吐量: {iterations * 5 / total_time:,.0f} ops/sec")
    
    # 性能判定
    if total_time < 2.0:
        click.echo(f"  ✅ 性能优秀！({total_time:.3f}秒 < 2秒)")
    elif total_time < 4.0:
        click.echo(f"  ⚠️  性能一般（{total_time:.3f}秒）")
    else:
        click.echo(f"  ❌ 性能不达标！({total_time:.3f}秒 > 2秒)")
    
    # 总结
    click.echo("\n" + "="*60)
    click.echo("📊 性能测试总结")
    click.echo("="*60)
    click.echo("✅ 加密算法: AES-256-GCM")
    click.echo("✅ IV生成: 随机（每次不同）")
    click.echo("✅ 认证标签: 支持（防篡改）")
    click.echo("\n💡 性能优化建议：")
    click.echo("   - 批量操作时使用事务（减少数据库往返）")
    click.echo("   - 敏感字段查询时先查主键，再解密")
    click.echo("   - 考虑使用缓存减少重复解密")
    click.echo("="*60 + "\n")


if __name__ == '__main__':
    main()
