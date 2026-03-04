# -*- coding: utf-8 -*-
"""
节假日模型和服务测试
"""

from datetime import date

from app.models.holiday import Holiday, HolidayService


class TestHolidayModel:
    """节假日模型测试"""

    def test_create_holiday(self, db):
        """测试创建节假日记录"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            description="农历新年",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        retrieved = db.query(Holiday).filter(Holiday.id == holiday.id).first()
        assert retrieved is not None
        assert retrieved.holiday_date == date(2024, 2, 10)
        assert retrieved.holiday_type == "HOLIDAY"
        assert retrieved.name == "春节"
        assert retrieved.is_active is True

    def test_create_workday(self, db):
        """测试创建调休工作日记录"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 4),
            year=2024,
            holiday_type="WORKDAY",
            name="春节调休",
            description="周日上班",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        retrieved = db.query(Holiday).filter(Holiday.id == holiday.id).first()
        assert retrieved is not None
        assert retrieved.holiday_type == "WORKDAY"

    def test_create_company_holiday(self, db):
        """测试创建公司假期记录"""
        holiday = Holiday(
            holiday_date=date(2024, 12, 25),
            year=2024,
            holiday_type="COMPANY",
            name="公司年会",
            description="全员团建活动",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        retrieved = db.query(Holiday).filter(Holiday.id == holiday.id).first()
        assert retrieved is not None
        assert retrieved.holiday_type == "COMPANY"

    def test_holiday_repr(self, db):
        """测试节假日对象的字符串表示"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        repr_str = repr(holiday)
        assert "Holiday" in repr_str
        assert "2024-02-10" in repr_str
        assert "春节" in repr_str


class TestHolidayServiceIsHoliday:
    """HolidayService.is_holiday 测试"""

    def test_is_holiday_true(self, db):
        """测试判断法定节假日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        is_holiday = HolidayService.is_holiday(db, date(2024, 2, 10))
        assert is_holiday is True

    def test_is_holiday_false(self, db):
        """测试判断非节假日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        is_holiday = HolidayService.is_holiday(db, date(2024, 2, 15))
        assert is_holiday is False

    def test_is_holiday_inactive(self, db):
        """测试判断已停用的节假日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=False,
        )
        db.add(holiday)
        db.commit()

        is_holiday = HolidayService.is_holiday(db, date(2024, 2, 10))
        assert is_holiday is False

    def test_is_holiday_workday_type(self, db):
        """测试调休工作日不是节假日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 4),
            year=2024,
            holiday_type="WORKDAY",
            name="春节调休",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        is_holiday = HolidayService.is_holiday(db, date(2024, 2, 4))
        assert is_holiday is False


class TestHolidayServiceIsWorkday:
    """HolidayService.is_workday 测试"""

    def test_is_workday_true(self, db):
        """测试判断调休工作日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 4),
            year=2024,
            holiday_type="WORKDAY",
            name="春节调休",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        is_workday = HolidayService.is_workday(db, date(2024, 2, 4))
        assert is_workday is True

    def test_is_workday_false(self, db):
        """测试判断非调休工作日"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        is_workday = HolidayService.is_workday(db, date(2024, 2, 10))
        assert is_workday is False

    def test_is_workday_normal_day(self, db):
        """测试判断普通工作日"""
        is_workday = HolidayService.is_workday(db, date(2024, 2, 20))
        assert is_workday is False


class TestHolidayServiceGetWorkType:
    """HolidayService.get_work_type 测试"""

    def test_get_work_type_holiday(self, db):
        """测试获取节假日类型"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        work_type = HolidayService.get_work_type(db, date(2024, 2, 10))
        assert work_type == "HOLIDAY"

    def test_get_work_type_workday_adjustment(self, db):
        """测试调休工作日返回NORMAL"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 4),  # 周日
            year=2024,
            holiday_type="WORKDAY",
            name="春节调休",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        work_type = HolidayService.get_work_type(db, date(2024, 2, 4))
        assert work_type == "NORMAL"

    def test_get_work_type_weekend(self, db):
        """测试周末返回WEEKEND"""
        # 2024-02-17 是周六
        work_type = HolidayService.get_work_type(db, date(2024, 2, 17))
        assert work_type == "WEEKEND"

    def test_get_work_type_normal(self, db):
        """测试普通工作日返回NORMAL"""
        # 2024-02-20 是周二
        work_type = HolidayService.get_work_type(db, date(2024, 2, 20))
        assert work_type == "NORMAL"


class TestHolidayServiceGetHolidayName:
    """HolidayService.get_holiday_name 测试"""

    def test_get_holiday_name_holiday(self, db):
        """测试获取节假日名称"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        name = HolidayService.get_holiday_name(db, date(2024, 2, 10))
        assert name == "春节"

    def test_get_holiday_name_workday(self, db):
        """测试获取调休工作日名称"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 4),
            year=2024,
            holiday_type="WORKDAY",
            name="春节调休",
            is_active=True,
        )
        db.add(holiday)
        db.commit()

        name = HolidayService.get_holiday_name(db, date(2024, 2, 4))
        assert name == "春节调休"

    def test_get_holiday_name_none(self, db):
        """测试获取不存在的节假日返回None"""
        name = HolidayService.get_holiday_name(db, date(2024, 2, 20))
        assert name is None

    def test_get_holiday_name_inactive(self, db):
        """测试获取已停用的节假日返回None"""
        holiday = Holiday(
            holiday_date=date(2024, 2, 10),
            year=2024,
            holiday_type="HOLIDAY",
            name="春节",
            is_active=False,
        )
        db.add(holiday)
        db.commit()

        name = HolidayService.get_holiday_name(db, date(2024, 2, 10))
        assert name is None
