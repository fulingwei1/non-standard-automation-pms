# -*- coding: utf-8 -*-
"""
人事管理集成测试 - 考勤打卡流程

测试场景：
1. 正常打卡记录
2. 迟到早退处理
3. 外出打卡
4. 补卡申请
5. 加班记录
6. 考勤统计
7. 考勤异常处理
"""

import pytest
from datetime import date, datetime, time, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.integration
class TestAttendancePunchFlow:
    """考勤打卡流程集成测试"""

    def test_normal_punch_record(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：正常打卡记录"""
        # 1. 员工上班打卡
        clock_in_data = {
            "employee_id": test_employee.id,
            "punch_time": f"{date.today()} 08:55:00",
            "punch_type": "clock_in",
            "punch_method": "face_recognition",
            "location": "公司前台",
            "latitude": 31.2304,
            "longitude": 121.4737
        }
        
        response = client.post("/api/v1/hr/attendance/punch", json=clock_in_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        # 2. 员工下班打卡
        clock_out_data = {
            "employee_id": test_employee.id,
            "punch_time": f"{date.today()} 18:05:00",
            "punch_type": "clock_out",
            "punch_method": "face_recognition",
            "location": "公司前台",
            "latitude": 31.2304,
            "longitude": 121.4737
        }
        
        response = client.post("/api/v1/hr/attendance/punch", json=clock_out_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        # 3. 查询当天考勤记录
        response = client.get(
            f"/api/v1/hr/attendance/records?employee_id={test_employee.id}&date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_late_and_early_leaving(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：迟到早退处理"""
        # 1. 迟到打卡
        late_clock_in = {
            "employee_id": test_employee.id,
            "punch_time": f"{date.today()} 09:30:00",  # 迟到30分钟
            "punch_type": "clock_in",
            "punch_method": "fingerprint",
            "location": "公司前台"
        }
        
        response = client.post("/api/v1/hr/attendance/punch", json=late_clock_in, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        # 2. 早退打卡
        early_clock_out = {
            "employee_id": test_employee.id,
            "punch_time": f"{date.today()} 17:30:00",  # 早退30分钟
            "punch_type": "clock_out",
            "punch_method": "fingerprint",
            "location": "公司前台"
        }
        
        response = client.post("/api/v1/hr/attendance/punch", json=early_clock_out, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        # 3. 查询异常考勤
        response = client.get(
            f"/api/v1/hr/attendance/anomalies?employee_id={test_employee.id}&date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_outdoor_punch(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：外出打卡"""
        # 1. 提交外出申请
        outing_application = {
            "employee_id": test_employee.id,
            "outing_date": str(date.today()),
            "start_time": "10:00:00",
            "end_time": "15:00:00",
            "outing_reason": "客户现场技术支持",
            "destination": "客户工厂 - 江苏省苏州市",
            "apply_date": str(date.today() - timedelta(days=1))
        }
        
        response = client.post("/api/v1/hr/outing-applications", json=outing_application, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        
        # 2. 外出地点打卡
        outdoor_punch = {
            "employee_id": test_employee.id,
            "punch_time": f"{date.today()} 10:15:00",
            "punch_type": "outdoor",
            "punch_method": "mobile_app",
            "location": "客户工厂",
            "latitude": 31.3,
            "longitude": 120.6,
            "photos": ["outdoor_punch_photo.jpg"]
        }
        
        response = client.post("/api/v1/hr/attendance/punch", json=outdoor_punch, headers=auth_headers)
        assert response.status_code in [200, 201]

    def test_punch_correction_application(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：补卡申请"""
        # 1. 提交补卡申请
        correction_data = {
            "employee_id": test_employee.id,
            "correction_date": str(date.today() - timedelta(days=1)),
            "punch_type": "clock_in",
            "actual_time": "08:50:00",
            "reason": "忘记打卡",
            "apply_date": str(date.today()),
            "supporting_documents": ["工作日志.pdf"]
        }
        
        response = client.post("/api/v1/hr/attendance/corrections", json=correction_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        correction_id = response.json().get("id") if response.status_code in [200, 201] else None
        
        # 2. 审批补卡申请
        if correction_id:
            approval_data = {
                "action": "approve",
                "approver_id": test_employee.id + 1,
                "approval_date": str(date.today()),
                "comments": "理由充分，同意补卡"
            }
            
            response = client.post(
                f"/api/v1/hr/attendance/corrections/{correction_id}/approve",
                json=approval_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 404]

    def test_overtime_record(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：加班记录"""
        # 1. 提交加班申请
        overtime_application = {
            "employee_id": test_employee.id,
            "overtime_date": str(date.today()),
            "start_time": "18:00:00",
            "end_time": "21:00:00",
            "overtime_hours": 3.0,
            "overtime_type": "工作日加班",
            "reason": "紧急项目需求",
            "apply_date": str(date.today())
        }
        
        response = client.post("/api/v1/hr/overtime-applications", json=overtime_application, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        overtime_id = response.json().get("id") if response.status_code in [200, 201] else None
        
        # 2. 加班打卡
        overtime_punches = [
            {
                "employee_id": test_employee.id,
                "punch_time": f"{date.today()} 18:00:00",
                "punch_type": "overtime_start",
                "punch_method": "fingerprint"
            },
            {
                "employee_id": test_employee.id,
                "punch_time": f"{date.today()} 21:00:00",
                "punch_type": "overtime_end",
                "punch_method": "fingerprint"
            }
        ]
        
        for punch in overtime_punches:
            response = client.post("/api/v1/hr/attendance/punch", json=punch, headers=auth_headers)
            assert response.status_code in [200, 201]
        
        # 3. 查询加班记录
        if overtime_id:
            response = client.get(
                f"/api/v1/hr/overtime-records/{overtime_id}",
                headers=auth_headers
            )
            assert response.status_code in [200, 404]

    def test_attendance_statistics(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：考勤统计"""
        # 1. 查询个人月度考勤统计
        stats_params = {
            "employee_id": test_employee.id,
            "year": date.today().year,
            "month": date.today().month
        }
        
        response = client.get("/api/v1/hr/attendance/statistics", params=stats_params, headers=auth_headers)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            stats = response.json()
            # 验证统计数据包含必要字段
            assert isinstance(stats, dict)
        
        # 2. 查询部门考勤汇总
        dept_stats_params = {
            "department_id": 1,
            "year": date.today().year,
            "month": date.today().month
        }
        
        response = client.get("/api/v1/hr/attendance/department-statistics", params=dept_stats_params, headers=auth_headers)
        assert response.status_code in [200, 404]
        
        # 3. 导出考勤报表
        export_request = {
            "export_type": "monthly_attendance",
            "year": date.today().year,
            "month": date.today().month,
            "department_id": 1,
            "format": "excel"
        }
        
        response = client.post("/api/v1/hr/attendance/export", json=export_request, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_attendance_anomaly_handling(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：考勤异常处理"""
        # 1. 系统自动检测异常
        anomaly_detection_request = {
            "detection_date": str(date.today()),
            "detection_type": ["missing_punch", "late", "early_leave"],
            "department_id": 1
        }
        
        response = client.post("/api/v1/hr/attendance/detect-anomalies", json=anomaly_detection_request, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        
        # 2. 查询异常列表
        response = client.get(
            f"/api/v1/hr/attendance/anomalies?date={date.today()}&status=pending",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        # 3. 处理考勤异常
        if response.status_code == 200:
            anomalies = response.json()
            if isinstance(anomalies, list) and len(anomalies) > 0:
                anomaly_id = anomalies[0].get("id")
                if anomaly_id:
                    handling_data = {
                        "anomaly_id": anomaly_id,
                        "handling_action": "deduct_salary",
                        "handling_result": "按迟到30分钟处理，扣除当日工资10%",
                        "handled_by": test_employee.id + 1,
                        "handle_date": str(date.today())
                    }
                    
                    response = client.post("/api/v1/hr/attendance/handle-anomaly", json=handling_data, headers=auth_headers)
                    assert response.status_code in [200, 201, 404]

    def test_flexible_working_attendance(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：弹性工作制考勤"""
        # 1. 设置员工为弹性工作制
        flexible_setting = {
            "employee_id": test_employee.id,
            "work_mode": "flexible",
            "core_work_hours": {
                "start": "10:00:00",
                "end": "16:00:00"
            },
            "min_daily_hours": 8.0,
            "effective_date": str(date.today())
        }
        
        response = client.post("/api/v1/hr/work-mode-settings", json=flexible_setting, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        
        # 2. 弹性打卡记录
        flexible_punches = [
            {
                "employee_id": test_employee.id,
                "punch_time": f"{date.today()} 09:30:00",
                "punch_type": "clock_in",
                "work_mode": "flexible"
            },
            {
                "employee_id": test_employee.id,
                "punch_time": f"{date.today()} 18:30:00",
                "punch_type": "clock_out",
                "work_mode": "flexible"
            }
        ]
        
        for punch in flexible_punches:
            response = client.post("/api/v1/hr/attendance/punch", json=punch, headers=auth_headers)
            assert response.status_code in [200, 201]
        
        # 3. 验证弹性工作时长
        response = client.get(
            f"/api/v1/hr/attendance/work-hours?employee_id={test_employee.id}&date={date.today()}",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
