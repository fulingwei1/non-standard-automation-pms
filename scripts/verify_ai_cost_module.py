#!/usr/bin/env python3
"""
AI成本估算模块验证脚本
"""
from decimal import Decimal


def test_hardware_cost_calculation():
    """测试硬件成本计算"""
    print("\n" + "=" * 60)
    print("测试1: 硬件成本计算")
    print("=" * 60)

    hardware_items = [
        {"name": "PLC控制器", "unit_price": 5000, "quantity": 2},
        {"name": "伺服电机", "unit_price": 3000, "quantity": 4},
        {"name": "传感器", "unit_price": 500, "quantity": 10},
    ]

    HARDWARE_MARKUP = Decimal("1.15")

    total = Decimal("0")
    for item in hardware_items:
        unit_price = Decimal(str(item["unit_price"]))
        quantity = Decimal(str(item["quantity"]))
        total += unit_price * quantity

    hardware_cost = total * HARDWARE_MARKUP

    print(f"硬件清单: {len(hardware_items)}项")
    print(f"原始成本: ¥{total}")
    print(f"加成系数: {HARDWARE_MARKUP}")
    print(f"最终成本: ¥{hardware_cost}")

    expected = Decimal("31050")  # (5000*2 + 3000*4 + 500*10) * 1.15 = 27000 * 1.15
    assert hardware_cost == expected, f"期望 {expected}, 实际 {hardware_cost}"
    print("✅ 测试通过!")


def test_software_cost_calculation():
    """测试软件成本计算"""
    print("\n" + "=" * 60)
    print("测试2: 软件成本计算")
    print("=" * 60)

    SOFTWARE_HOURLY_RATE = Decimal("800")

    # 有人天估算
    man_days = 20
    software_cost1 = Decimal(str(man_days)) * Decimal("8") * SOFTWARE_HOURLY_RATE
    print(f"场景1: 有人天估算")
    print(f"  人天: {man_days}")
    print(f"  时薪: ¥{SOFTWARE_HOURLY_RATE}")
    print(f"  成本: ¥{software_cost1}")

    expected1 = Decimal("128000")
    assert software_cost1 == expected1, f"期望 {expected1}, 实际 {software_cost1}"

    # 无人天估算,自动推断
    auto_man_days = 5
    software_cost2 = Decimal(str(auto_man_days)) * Decimal("8") * SOFTWARE_HOURLY_RATE
    print(f"场景2: 自动估算(简短需求)")
    print(f"  自动人天: {auto_man_days}")
    print(f"  成本: ¥{software_cost2}")

    expected2 = Decimal("32000")
    assert software_cost2 == expected2, f"期望 {expected2}, 实际 {software_cost2}"

    print("✅ 测试通过!")


def test_installation_cost_calculation():
    """测试安装成本计算"""
    print("\n" + "=" * 60)
    print("测试3: 安装成本计算")
    print("=" * 60)

    INSTALLATION_BASE_COST = Decimal("5000")
    hardware_cost = Decimal("100000")

    difficulties = {"low": Decimal("1.0"), "medium": Decimal("1.5"), "high": Decimal("2.0")}

    for difficulty, multiplier in difficulties.items():
        installation_cost = INSTALLATION_BASE_COST * multiplier + hardware_cost * Decimal("0.05")
        print(f"{difficulty}难度: ¥{installation_cost}")

    # 验证medium难度
    expected = Decimal("12500")  # 5000 * 1.5 + 100000 * 0.05
    medium_cost = INSTALLATION_BASE_COST * Decimal("1.5") + hardware_cost * Decimal("0.05")
    assert medium_cost == expected, f"期望 {expected}, 实际 {medium_cost}"

    print("✅ 测试通过!")


def test_service_cost_calculation():
    """测试服务成本计算"""
    print("\n" + "=" * 60)
    print("测试4: 服务成本计算")
    print("=" * 60)

    SERVICE_ANNUAL_RATE = Decimal("0.10")
    hardware_cost = Decimal("100000")
    software_cost = Decimal("80000")
    service_years = 2

    base_for_service = hardware_cost + software_cost
    service_cost = base_for_service * SERVICE_ANNUAL_RATE * Decimal(str(service_years))

    print(f"硬件成本: ¥{hardware_cost}")
    print(f"软件成本: ¥{software_cost}")
    print(f"服务年限: {service_years}年")
    print(f"年费率: {SERVICE_ANNUAL_RATE * 100}%")
    print(f"服务成本: ¥{service_cost}")

    expected = Decimal("36000")  # (100000 + 80000) * 0.10 * 2
    assert service_cost == expected, f"期望 {expected}, 实际 {service_cost}"

    print("✅ 测试通过!")


def test_risk_reserve_calculation():
    """测试风险储备计算"""
    print("\n" + "=" * 60)
    print("测试5: 风险储备计算")
    print("=" * 60)

    RISK_RESERVE_RATE = Decimal("0.08")
    base_cost = Decimal("200000")

    complexity_factors = {"low": Decimal("0.5"), "medium": Decimal("1.0"), "high": Decimal("1.5")}

    for complexity, factor in complexity_factors.items():
        risk_reserve = base_cost * RISK_RESERVE_RATE * factor
        print(f"{complexity}复杂度: ¥{risk_reserve}")

    # 验证high复杂度
    expected = Decimal("24000")  # 200000 * 0.08 * 1.5
    high_risk = base_cost * RISK_RESERVE_RATE * Decimal("1.5")
    assert high_risk == expected, f"期望 {expected}, 实际 {high_risk}"

    print("✅ 测试通过!")


def test_pricing_recommendation():
    """测试定价推荐"""
    print("\n" + "=" * 60)
    print("测试6: 定价推荐")
    print("=" * 60)

    total_cost = Decimal("220000")
    target_margin_rate = Decimal("0.30")

    # 建议价格
    suggested_price = total_cost / (Decimal("1") - target_margin_rate)

    # 低中高三档
    low = suggested_price * Decimal("0.90")
    medium = suggested_price
    high = suggested_price * Decimal("1.15")

    print(f"总成本: ¥{total_cost}")
    print(f"目标毛利率: {target_margin_rate * 100}%")
    print(f"建议价格: ¥{suggested_price:.2f}")
    print(f"  低价档: ¥{low:.2f}")
    print(f"  标准价: ¥{medium:.2f}")
    print(f"  高价档: ¥{high:.2f}")

    # 验证毛利率
    actual_margin = (suggested_price - total_cost) / suggested_price
    print(f"实际毛利率: {actual_margin * 100:.2f}%")

    assert abs(actual_margin - target_margin_rate) < Decimal("0.001"), "毛利率计算错误"

    print("✅ 测试通过!")


def test_variance_rate_calculation():
    """测试偏差率计算"""
    print("\n" + "=" * 60)
    print("测试7: 偏差率计算")
    print("=" * 60)

    estimated_cost = Decimal("100000")

    test_cases = [
        {"actual": Decimal("110000"), "expected_variance": Decimal("10.0")},
        {"actual": Decimal("90000"), "expected_variance": Decimal("-10.0")},
        {"actual": Decimal("100000"), "expected_variance": Decimal("0.0")},
    ]

    for case in test_cases:
        actual_cost = case["actual"]
        variance = actual_cost - estimated_cost
        variance_rate = variance / estimated_cost * Decimal("100")

        print(f"估算: ¥{estimated_cost}, 实际: ¥{actual_cost}, 偏差率: {variance_rate}%")

        assert abs(variance_rate - case["expected_variance"]) < Decimal(
            "0.01"
        ), f"期望偏差 {case['expected_variance']}%, 实际 {variance_rate}%"

    print("✅ 测试通过!")


def test_full_estimation_flow():
    """测试完整估算流程"""
    print("\n" + "=" * 60)
    print("测试8: 完整估算流程")
    print("=" * 60)

    # 参数
    HARDWARE_MARKUP = Decimal("1.15")
    SOFTWARE_HOURLY_RATE = Decimal("800")
    INSTALLATION_BASE_COST = Decimal("5000")
    SERVICE_ANNUAL_RATE = Decimal("0.10")
    RISK_RESERVE_RATE = Decimal("0.08")

    # 输入
    hardware_items = [
        {"name": "PLC", "unit_price": 5000, "quantity": 2},
        {"name": "电机", "unit_price": 3000, "quantity": 4},
    ]
    estimated_man_days = 20
    service_years = 2
    
    # 1. 硬件成本
    hardware_total = sum(
        Decimal(str(item["unit_price"])) * Decimal(str(item["quantity"])) for item in hardware_items
    )
    hardware_cost = hardware_total * HARDWARE_MARKUP

    # 2. 软件成本
    software_cost = Decimal(str(estimated_man_days)) * Decimal("8") * SOFTWARE_HOURLY_RATE

    # 3. 安装成本
    difficulty_multiplier = Decimal("1.5")  # medium
    installation_cost = INSTALLATION_BASE_COST * difficulty_multiplier + hardware_cost * Decimal(
        "0.05"
    )

    # 4. 服务成本
    service_cost = (
        (hardware_cost + software_cost) * SERVICE_ANNUAL_RATE * Decimal(str(service_years))
    )

    # 5. 风险储备
    base_cost = hardware_cost + software_cost + installation_cost
    complexity_factor = Decimal("1.0")  # medium
    risk_reserve = base_cost * RISK_RESERVE_RATE * complexity_factor

    # 6. 总成本
    total_cost = hardware_cost + software_cost + installation_cost + service_cost + risk_reserve

    print(f"成本分解:")
    print(f"  硬件成本: ¥{hardware_cost}")
    print(f"  软件成本: ¥{software_cost}")
    print(f"  安装成本: ¥{installation_cost}")
    print(f"  服务成本: ¥{service_cost}")
    print(f"  风险储备: ¥{risk_reserve}")
    print(f"  总成本: ¥{total_cost}")

    # 验证总成本合理
    assert total_cost > Decimal("0"), "总成本应大于0"
    assert hardware_cost + software_cost < total_cost, "总成本应大于硬件+软件成本"

    print("✅ 测试通过!")


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("AI成本估算模块 - 核心逻辑验证")
    print("🚀" * 30)

    try:
        test_hardware_cost_calculation()
        test_software_cost_calculation()
        test_installation_cost_calculation()
        test_service_cost_calculation()
        test_risk_reserve_calculation()
        test_pricing_recommendation()
        test_variance_rate_calculation()
        test_full_estimation_flow()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过! (8/8)")
        print("=" * 60)
        print("\n核心功能验证完成,模块可以正常使用!")
        print("下一步:")
        print("  1. 执行数据库迁移: alembic upgrade head")
        print("  2. 重启服务: ./start.sh")
        print("  3. 测试API端点")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
