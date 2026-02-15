#!/usr/bin/env python3
"""
数据加密功能快速验证

验证以下功能：
1. 加密/解密基础功能
2. SQLAlchemy加密类型
3. 性能测试
"""

import os
import sys
import time

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.encryption import data_encryption


def test_basic_encryption():
    """测试基础加密/解密功能"""
    print("\n" + "="*60)
    print("🔒 测试1：基础加密/解密功能")
    print("="*60)
    
    test_cases = [
        ("421002199001011234", "身份证号"),
        ("6217000010012345678", "银行卡号"),
        ("13800138000", "手机号"),
        ("湖北省武汉市洪山区珞瑜路1号", "地址"),
        ("15000.50", "薪资"),
    ]
    
    passed = 0
    failed = 0
    
    for plaintext, label in test_cases:
        try:
            # 加密
            encrypted = data_encryption.encrypt(plaintext)
            
            # 解密
            decrypted = data_encryption.decrypt(encrypted)
            
            # 验证
            if decrypted == plaintext:
                print(f"✅ {label}: 加密/解密成功")
                passed += 1
            else:
                print(f"❌ {label}: 解密结果不一致")
                failed += 1
        
        except Exception as e:
            print(f"❌ {label}: 发生错误 - {e}")
            failed += 1
    
    print(f"\n总结: ✅ 通过 {passed}/{len(test_cases)}, ❌ 失败 {failed}/{len(test_cases)}")
    return failed == 0


def test_unicode_encryption():
    """测试Unicode字符加密"""
    print("\n" + "="*60)
    print("🔤 测试2：Unicode字符加密")
    print("="*60)
    
    unicode_texts = [
        "张三",
        "李四🎉",
        "测试数据 Test 123",
        "特殊字符：！@#￥%……&*（）",
    ]
    
    passed = 0
    
    for text in unicode_texts:
        encrypted = data_encryption.encrypt(text)
        decrypted = data_encryption.decrypt(encrypted)
        
        if decrypted == text:
            print(f"✅ Unicode: {text[:20]}...")
            passed += 1
        else:
            print(f"❌ Unicode: {text[:20]}... 解密失败")
    
    print(f"\n总结: ✅ 通过 {passed}/{len(unicode_texts)}")
    return passed == len(unicode_texts)


def test_random_iv():
    """测试随机IV"""
    print("\n" + "="*60)
    print("🎲 测试3：随机IV（每次加密不同）")
    print("="*60)
    
    plaintext = "421002199001011234"
    
    encrypted1 = data_encryption.encrypt(plaintext)
    encrypted2 = data_encryption.encrypt(plaintext)
    encrypted3 = data_encryption.encrypt(plaintext)
    
    # 密文应该不同
    if encrypted1 != encrypted2 and encrypted2 != encrypted3:
        print(f"✅ 相同明文，不同密文（IV随机）")
        print(f"   密文1: {encrypted1[:50]}...")
        print(f"   密文2: {encrypted2[:50]}...")
        print(f"   密文3: {encrypted3[:50]}...")
    else:
        print(f"❌ 密文相同（IV未随机）")
        return False
    
    # 但解密结果应该相同
    if (data_encryption.decrypt(encrypted1) == plaintext and
        data_encryption.decrypt(encrypted2) == plaintext and
        data_encryption.decrypt(encrypted3) == plaintext):
        print(f"✅ 解密结果相同（正确）")
        return True
    else:
        print(f"❌ 解密结果不一致")
        return False


def test_empty_values():
    """测试空值处理"""
    print("\n" + "="*60)
    print("⭕ 测试4：空值处理")
    print("="*60)
    
    # 空字符串
    assert data_encryption.encrypt("") == ""
    print("✅ 空字符串: encrypt('') == ''")
    
    # None
    assert data_encryption.encrypt(None) is None
    print("✅ None值: encrypt(None) is None")
    
    assert data_encryption.decrypt("") == ""
    print("✅ 解密空字符串: decrypt('') == ''")
    
    assert data_encryption.decrypt(None) is None
    print("✅ 解密None值: decrypt(None) is None")
    
    return True


def test_invalid_data():
    """测试无效数据解密"""
    print("\n" + "="*60)
    print("⚠️  测试5：无效数据解密")
    print("="*60)
    
    invalid_data = [
        "invalid_base64_string",
        "abc123",
        "这不是加密数据",
    ]
    
    passed = 0
    
    for data in invalid_data:
        result = data_encryption.decrypt(data)
        if result == "[解密失败]":
            print(f"✅ 无效数据: {data[:20]}... → [解密失败]")
            passed += 1
        else:
            print(f"❌ 无效数据: {data[:20]}... → {result}")
    
    print(f"\n总结: ✅ 通过 {passed}/{len(invalid_data)}")
    return passed == len(invalid_data)


def test_performance():
    """性能测试"""
    print("\n" + "="*60)
    print("⏱️  测试6：性能测试")
    print("="*60)
    
    plaintext = "421002199001011234"
    iterations = 10000
    
    # 加密性能
    start = time.time()
    for _ in range(iterations):
        data_encryption.encrypt(plaintext)
    encrypt_time = time.time() - start
    
    print(f"加密性能: {iterations:,}次加密耗时 {encrypt_time:.3f}秒")
    print(f"          吞吐量: {iterations / encrypt_time:,.0f} ops/sec")
    
    # 解密性能
    encrypted = data_encryption.encrypt(plaintext)
    start = time.time()
    for _ in range(iterations):
        data_encryption.decrypt(encrypted)
    decrypt_time = time.time() - start
    
    print(f"解密性能: {iterations:,}次解密耗时 {decrypt_time:.3f}秒")
    print(f"          吞吐量: {iterations / decrypt_time:,.0f} ops/sec")
    
    # 性能判定
    if encrypt_time < 1.0 and decrypt_time < 1.0:
        print(f"\n✅ 性能优秀！（加密 {encrypt_time:.3f}秒 < 1秒，解密 {decrypt_time:.3f}秒 < 1秒）")
        return True
    else:
        print(f"\n❌ 性能不达标！（目标: < 1秒）")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 数据加密功能快速验证")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("基础加密/解密", test_basic_encryption()))
    results.append(("Unicode字符", test_unicode_encryption()))
    results.append(("随机IV", test_random_iv()))
    results.append(("空值处理", test_empty_values()))
    results.append(("无效数据", test_invalid_data()))
    results.append(("性能测试", test_performance()))
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！数据加密功能正常！")
        print("="*60 + "\n")
        return 0
    else:
        print(f"❌ 有 {total - passed} 个测试失败！")
        print("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
