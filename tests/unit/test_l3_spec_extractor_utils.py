# -*- coding: utf-8 -*-
"""
L3组 单元测试 - app/utils/spec_extractor/utils.py
extract_key_parameters 是纯逻辑函数，直接传字符串测试。
"""

import pytest

from app.utils.spec_extractor.utils import extract_key_parameters


class TestExtractKeyParametersVoltage:
    """电压提取"""

    def test_voltage_plain(self):
        params = extract_key_parameters("220V")
        assert "voltage" in params
        assert params["voltage"] == "220"

    def test_voltage_dc(self):
        params = extract_key_parameters("24VDC")
        assert params["voltage"] == "24"

    def test_voltage_ac(self):
        params = extract_key_parameters("110VAC")
        assert params["voltage"] == "110"

    def test_voltage_decimal(self):
        params = extract_key_parameters("3.3V")
        assert params["voltage"] == "3.3"

    def test_voltage_chinese(self):
        params = extract_key_parameters("电压220伏")
        assert params["voltage"] == "220"

    def test_no_voltage(self):
        params = extract_key_parameters("纯文字描述")
        assert "voltage" not in params


class TestExtractKeyParametersCurrent:
    """电流提取"""

    def test_current_amps(self):
        params = extract_key_parameters("5A")
        assert "current" in params
        assert params["current"] == "5"

    def test_current_milliamps(self):
        params = extract_key_parameters("500mA")
        assert params["current"] == "500"

    def test_current_decimal(self):
        params = extract_key_parameters("0.5A")
        assert params["current"] == "0.5"

    def test_current_chinese(self):
        params = extract_key_parameters("电流10安")
        assert params["current"] == "10"

    def test_no_current(self):
        params = extract_key_parameters("220V 100W")
        assert "current" not in params


class TestExtractKeyParametersAccuracy:
    """精度/公差提取"""

    def test_accuracy_percent(self):
        params = extract_key_parameters("±0.1%")
        assert "accuracy" in params
        assert params["accuracy"] == "0.1"

    def test_accuracy_temperature(self):
        params = extract_key_parameters("±2℃")
        assert params["accuracy"] == "2"

    def test_accuracy_millimeter(self):
        params = extract_key_parameters("±0.01mm")
        assert params["accuracy"] == "0.01"

    def test_accuracy_label(self):
        params = extract_key_parameters("精度：0.5")
        assert params["accuracy"] == "0.5"

    def test_no_accuracy(self):
        params = extract_key_parameters("220V 5A")
        assert "accuracy" not in params


class TestExtractKeyParametersTemperature:
    """温度范围提取"""

    def test_temp_range_tilde(self):
        params = extract_key_parameters("-20~60℃")
        assert "temp_min" in params
        assert "temp_max" in params
        assert params["temp_min"] == "-20"
        assert params["temp_max"] == "60"

    def test_temp_range_dash(self):
        params = extract_key_parameters("0-50℃")
        assert params["temp_min"] == "0"
        assert params["temp_max"] == "50"

    def test_temp_with_label(self):
        params = extract_key_parameters("温度：-10~45")
        assert params["temp_min"] == "-10"
        assert params["temp_max"] == "45"

    def test_no_temp(self):
        params = extract_key_parameters("220V 5A 100W")
        assert "temp_min" not in params


class TestExtractKeyParametersPower:
    """功率提取"""

    def test_power_watts(self):
        params = extract_key_parameters("100W")
        assert "power" in params
        assert params["power"] == "100"

    def test_power_kilowatts(self):
        params = extract_key_parameters("1.5kW")
        assert params["power"] == "1.5"

    def test_power_milliwatts(self):
        params = extract_key_parameters("500mW")
        assert params["power"] == "500"

    def test_power_chinese(self):
        params = extract_key_parameters("功率50瓦")
        assert params["power"] == "50"

    def test_no_power(self):
        params = extract_key_parameters("仅有温度说明")
        assert "power" not in params


class TestExtractKeyParametersFrequency:
    """频率提取"""

    def test_frequency_50hz(self):
        params = extract_key_parameters("50Hz")
        assert "frequency" in params
        assert params["frequency"] == "50"

    def test_frequency_60hz(self):
        params = extract_key_parameters("60Hz")
        assert params["frequency"] == "60"

    def test_frequency_chinese(self):
        params = extract_key_parameters("频率50赫兹")
        assert params["frequency"] == "50"

    def test_no_frequency(self):
        params = extract_key_parameters("220V 5A")
        assert "frequency" not in params


class TestExtractKeyParametersSize:
    """尺寸提取"""

    def test_size_3d(self):
        params = extract_key_parameters("100x200x50mm")
        assert "length" in params
        assert "width" in params
        assert "height" in params
        assert params["length"] == "100"
        assert params["width"] == "200"
        assert params["height"] == "50"

    def test_diameter(self):
        params = extract_key_parameters("直径：50mm")
        assert "diameter" in params
        assert params["diameter"] == "50"

    def test_no_size(self):
        params = extract_key_parameters("220V 5A")
        assert "length" not in params
        assert "diameter" not in params


class TestExtractKeyParametersMixed:
    """复合参数提取"""

    def test_multiple_params(self):
        params = extract_key_parameters("220V 5A 100W 50Hz")
        assert "voltage" in params
        assert "current" in params
        assert "power" in params
        assert "frequency" in params

    def test_empty_string(self):
        params = extract_key_parameters("")
        assert params == {}

    def test_only_text_no_params(self):
        params = extract_key_parameters("普通文字说明，没有数值参数")
        assert len(params) == 0

    def test_voltage_and_temperature(self):
        params = extract_key_parameters("24V -20~70℃")
        assert params["voltage"] == "24"
        assert params["temp_min"] == "-20"
        assert params["temp_max"] == "70"
