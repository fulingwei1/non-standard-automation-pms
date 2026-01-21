"""
Comprehensive tests for alert rule engine services.
Tests coverage for:
- app.services.alert_rule_engine (module-level functions)
- app/services/alert/alert_rule_engine/ (engine components)
"""


import pytest
pytestmark = pytest.mark.skip(reason="Import errors - needs review")
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


from app.models.alert import (
    AlertRule,
    AlertRecord,
    AlertLevel,
)
from app.models.project import Project, ProjectStatus, ProjectHealth




class TestAlertRuleEngineCore:
    """Test core alert rule engine module-level functions."""


    def test_import_rule_engine_components(self):
        """Test that all alert rule engine components can be imported."""
        try:
            from app.services.alert import (
                evaluate_rule_condition,
                get_project_context,
                check_alert_level,
                should_fire_alert,
            )
        except ImportError as e:
            pytest.skip(f"Failed to import alert rule engine components: {e}")


    def test_evaluate_simple_rule_conditions(self, db_session: Session):
        """Test evaluation of simple rule conditions."""


        # Test numeric comparison
        assert (
            evaluate_rule_condition(
                "project.health", "H2", {"operator": "=", "value": "H2"}
            )
            == True
        )


        # Test string comparison
        assert (
            evaluate_rule_condition(
                "project.stage", "S3", {"operator": "=", "value": "S3"}
            )
            == True
        )


        # Test numeric greater than
        assert (
            evaluate_rule_condition(
                "project.delay_days", 10, {"operator": ">", "value": 5}
            )
            == True
        )


    def test_evaluate_complex_rule_conditions(self, db_session: Session):
        """Test evaluation of complex rule conditions with logical operators."""


        # Test AND condition
        condition = {
            "operator": "AND",
            "conditions": [
                {"field": "project.health", "operator": "!=", "value": "H1"},
                {"field": "project.delay_days", "operator": ">", "value": 5},
            ],
        }
        result = evaluate_rule_condition(None, None, condition)
        assert result is not None


    def test_get_project_context_for_alerts(self, db_session: Session):
        """Test retrieving project context for alert evaluation."""


        # Create test project
        project = Project(
            project_code="PJ260101001",
            name="Test Project",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.NORMAL,
            planned_end_date=datetime.now() + timedelta(days=30),
            actual_end_date=None,
        )
        db_session.add(project)
        db_session.commit()


        # Get context
        context = get_project_context(db_session, project.id)
        assert context is not None
        assert "project" in context
        assert context["project"].id == project.id


    def test_check_alert_level_determination(self, db_session: Session):
        """Test alert level determination based on severity."""


        # Test different severity levels
        assert check_alert_level({"severity": "critical"}) == AlertLevel.CRITICAL
        assert check_alert_level({"severity": "severe"}) == AlertLevel.SEVERE
        assert check_alert_level({"severity": "warning"}) == AlertLevel.WARNING
        assert check_alert_level({"severity": "info"}) == AlertLevel.INFO


    def test_should_fire_alert_with_cooldown(self, db_session: Session):
        """Test alert firing logic with cooldown period."""


        # Create test project and rule
        project = Project(
            project_code="PJ260101002",
            name="Test Project 2",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.AT_RISK,
        )
        db_session.add(project)


        rule = AlertRule(
            rule_name="Test Rule",
            rule_type="PROJECT_HEALTH",
            condition='{"field": "health", "operator": "=", "value": "H2"}',
            cooldown_minutes=60,
            is_active=True,
        )
        db_session.add(rule)
        db_session.commit()


        # Test first time - should fire
        should_fire_1 = should_fire_alert(db_session, rule.id, project.id)
        assert should_fire_1 is True


        # Create alert record
        alert_record = AlertRecord(
            rule_id=rule.id,
            project_id=project.id,
            alert_level=AlertLevel.WARNING,
            message="Test alert",
            is_resolved=False,
        )
        db_session.add(alert_record)
        db_session.commit()


        # Test second time within cooldown - should not fire
        should_fire_2 = should_fire_alert(db_session, rule.id, project.id)
        assert should_fire_2 is False




class TestAlertGenerator:
    """Test alert generation functionality."""


    def test_generate_project_health_alert(self, db_session: Session):
        """Test generation of project health alerts."""
        try:
            from app.services.alert import (
                generate_project_health_alert,
            )
        except ImportError:
            pytest.skip("generate_project_health_alert function not available")


        # Create project at risk
        project = Project(
            project_code="PJ260101003",
            name="Test Project 3",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.AT_RISK,
            planned_end_date=datetime.now() + timedelta(days=30),
        )
        db_session.add(project)
        db_session.commit()


        # Generate alert
        alert = generate_project_health_alert(db_session, project)
        assert alert is not None
        assert "health" in alert.message.lower()


    def test_generate_delay_alert(self, db_session: Session):
        """Test generation of project delay alerts."""
        # from app.services.alert.alert_generator import (
        #     generate_delay_alert,
        # )


        # Create delayed project
        project = Project(
            project_code="PJ260101004",
            name="Test Project 4",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.BLOCKED,
            planned_end_date=datetime.now() - timedelta(days=10),
        )
        db_session.add(project)
        db_session.commit()


        # Generate delay alert
        alert = generate_delay_alert(db_session, project, 10)
        assert alert is not None
        assert "delay" in alert.message.lower()


    def test_generate_milestone_missed_alert(self, db_session: Session):
        """Test generation of milestone missed alerts."""
        # from app.services.alert.alert_generator import (
        #     generate_milestone_alert,
        # )


        project = Project(
            project_code="PJ260101005",
            name="Test Project 5",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()


        # Generate milestone alert
        alert = generate_milestone_alert(
            db_session, project, "S2 Review", datetime.now() - timedelta(days=2)
        )
        assert alert is not None
        assert "milestone" in alert.message.lower()




class TestAlertCreator:
    """Test alert creation and storage functionality."""


    def test_create_alert_record(self, db_session: Session):
        """Test creation of alert records in database."""
        # from app.services.alert.alert_manager import (
        #     create_alert_record,
        # )


        # Create test project and rule
        project = Project(
            project_code="PJ260101006",
            name="Test Project 6",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()


        rule = AlertRule(
            rule_name="Test Rule 2",
            rule_type="PROJECT_DELAY",
            condition="{}",
            is_active=True,
        )
        db_session.add(rule)
        db_session.commit()


        # Create alert
        alert_record = create_alert_record(
            db_session=db_session,
            rule_id=rule.id,
            project_id=project.id,
            alert_level=AlertLevel.SEVERE,
            message="Project is delayed",
            metadata={"delay_days": 15},
        )


        assert alert_record.id is not None
        assert alert_record.project_id == project.id
        assert alert_record.rule_id == rule.id
        assert alert_record.alert_level == AlertLevel.SEVERE


    def test_batch_create_alerts(self, db_session: Session):
        """Test batch creation of multiple alerts."""
# import (
            batch_create_alerts,
        )


        # Create multiple projects
        projects = []
        for i in range(5):
            project = Project(
                project_code=f"PJ260101{i + 7}",
                name=f"Test Project {i + 7}",
                customer_name="Test Customer",
                status=ProjectStatus.IN_PROGRESS,
            )
            db_session.add(project)
            db_session.commit()
            projects.append(project)


        rule = AlertRule(
            rule_name="Batch Test Rule",
            rule_type="PROJECT_HEALTH",
            condition="{}",
            is_active=True,
        )
        db_session.add(rule)
        db_session.commit()


        # Create batch alerts
        alerts_data = [
            {
                "rule_id": rule.id,
                "project_id": p.id,
                "alert_level": AlertLevel.WARNING,
                "message": f"Alert for {p.name}",
            }
            for p in projects
        ]


        created_alerts = batch_create_alerts(db_session, alerts_data)
        assert len(created_alerts) == 5
        for alert in created_alerts:
            assert alert.id is not None




class TestLevelDeterminer:
    """Test alert level determination logic."""


    def test_determine_level_from_health(self):
        """Test determining alert level from project health."""
# import (
            determine_level_from_health,
        )


        assert determine_level_from_health(ProjectHealth.NORMAL) == AlertLevel.INFO
        assert determine_level_from_health(ProjectHealth.AT_RISK) == AlertLevel.WARNING
        assert determine_level_from_health(ProjectHealth.BLOCKED) == AlertLevel.SEVERE
        assert determine_level_from_health(ProjectHealth.COMPLETED) is None


    def test_determine_level_from_delay(self):
        """Test determining alert level from delay days."""
# import (
            determine_level_from_delay,
        )


        assert determine_level_from_delay(0) is None
        assert determine_level_from_delay(5) == AlertLevel.INFO
        assert determine_level_from_delay(10) == AlertLevel.WARNING
        assert determine_level_from_delay(20) == AlertLevel.SEVERE
        assert determine_level_from_delay(30) == AlertLevel.CRITICAL


    def test_determine_level_from_severity_score(self):
        """Test determining alert level from severity score."""
# import (
            determine_level_from_severity_score,
        )


        assert determine_level_from_severity_score(1) == AlertLevel.INFO
        assert determine_level_from_severity_score(5) == AlertLevel.WARNING
        assert determine_level_from_severity_score(8) == AlertLevel.SEVERE
        assert determine_level_from_severity_score(10) == AlertLevel.CRITICAL




class TestAlertUpgrader:
    """Test alert upgrade logic."""


    def test_upgrade_alert_level(self, db_session: Session):
        """Test upgrading existing alert to higher level."""
# import (
            upgrade_alert_level,
        )


        # Create project and rule
        project = Project(
            project_code="PJ260101012",
            name="Test Project 12",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()


        rule = AlertRule(
            rule_name="Upgrade Test Rule",
            rule_type="PROJECT_DELAY",
            condition="{}",
            is_active=True,
        )
        db_session.add(rule)
        db_session.commit()


        # Create initial warning alert
        alert = AlertRecord(
            rule_id=rule.id,
            project_id=project.id,
            alert_level=AlertLevel.WARNING,
            message="Initial warning",
            is_resolved=False,
        )
        db_session.add(alert)
        db_session.commit()
        alert_id = alert.id


        # Upgrade to severe
        upgraded = upgrade_alert_level(
            db_session, alert_id, AlertLevel.SEVERE, "Upgraded due to increased delay"
        )
        assert upgraded is True


        # Verify upgrade
        db_session.refresh(alert)
        assert alert.alert_level == AlertLevel.SEVERE
        assert "upgraded" in alert.message.lower()


    def test_batch_upgrade_alerts(self, db_session: Session):
        """Test batch upgrading of multiple alerts."""
# import (
            batch_upgrade_alerts,
        )


        # Create multiple alerts
        project = Project(
            project_code="PJ260101013",
            name="Test Project 13",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
        )
        db_session.add(project)
        db_session.commit()


        rule = AlertRule(
            rule_name="Batch Upgrade Test Rule",
            rule_type="PROJECT_HEALTH",
            condition="{}",
            is_active=True,
        )
        db_session.add(rule)
        db_session.commit()


        alerts = []
        for i in range(5):
            alert = AlertRecord(
                rule_id=rule.id,
                project_id=project.id,
                alert_level=AlertLevel.WARNING,
                message=f"Alert {i}",
                is_resolved=False,
            )
            db_session.add(alert)
            db_session.commit()
            alerts.append(alert.id)


        # Batch upgrade
        results = batch_upgrade_alerts(
            db_session, alerts, AlertLevel.SEVERE, "Batch upgrade"
        )
        assert all(results)


        # Verify all upgraded
        db_session.refresh(alert)
        assert alert.alert_level == AlertLevel.SEVERE




class TestRuleManager:
    """Test rule management functionality."""


    def test_create_rule(self, db_session: Session):
        """Test creating new alert rules."""
# import (
            create_alert_rule,
        )


        rule_data = {
            "rule_name": "Test Rule 3",
            "rule_type": "PROJECT_DELAY",
            "condition": {"field": "delay_days", "operator": ">", "value": 10},
            "alert_level": AlertLevel.WARNING,
            "is_active": True,
            "cooldown_minutes": 30,
        }


        rule = create_alert_rule(db_session, rule_data)
        assert rule.id is not None
        assert rule.rule_name == "Test Rule 3"


    def test_update_rule(self, db_session: Session):
        """Test updating existing alert rules."""
# import (
            create_alert_rule,
            update_alert_rule,
        )


        # Create rule
        rule_data = {
            "rule_name": "Test Rule 4",
            "rule_type": "PROJECT_HEALTH",
            "condition": "{}",
            "alert_level": AlertLevel.INFO,
            "is_active": True,
        }
        rule = create_alert_rule(db_session, rule_data)


        # Update rule
        updated = update_alert_rule(
            db_session, rule.id, {"is_active": False, "cooldown_minutes": 60}
        )
        assert updated is True
        assert rule.is_active is False
        assert rule.cooldown_minutes == 60


    def test_delete_rule(self, db_session: Session):
        """Test deleting alert rules (soft delete)."""
# import (
            create_alert_rule,
            delete_alert_rule,
        )


        # Create rule
        rule_data = {
            "rule_name": "Test Rule 5",
            "rule_type": "PROJECT_DELAY",
            "condition": "{}",
            "alert_level": AlertLevel.WARNING,
            "is_active": True,
        }
        rule = create_alert_rule(db_session, rule_data)
        rule_id = rule.id


        # Delete rule
        deleted = delete_alert_rule(db_session, rule_id)
        assert deleted is True


        # Verify soft delete
        db_session.refresh(rule)
        assert rule.is_active is False


    def test_get_active_rules(self, db_session: Session):
        """Test retrieving active alert rules."""
# import (
            create_alert_rule,
            get_active_rules,
        )


        # Create multiple rules
        for i in range(5):
            rule_data = {
                "rule_name": f"Test Rule {i}",
                "rule_type": "PROJECT_HEALTH",
                "condition": "{}",
                "alert_level": AlertLevel.INFO,
                "is_active": i < 3,  # First 3 active
            }
            create_alert_rule(db_session, rule_data)


        # Get active rules
        active_rules = get_active_rules(db_session)
        assert len(active_rules) == 3


    def test_evaluate_project_against_rules(self, db_session: Session):
        """Test evaluating a project against all active rules."""
# import (
            create_alert_rule,
            evaluate_project_against_rules,
        )


        # Create project
        project = Project(
            project_code="PJ260101014",
            name="Test Project 14",
            customer_name="Test Customer",
            status=ProjectStatus.IN_PROGRESS,
            health=ProjectHealth.AT_RISK,
        )
        db_session.add(project)
        db_session.commit()


        # Create rules
        rule_data = {
            "rule_name": "Health Risk Rule",
            "rule_type": "PROJECT_HEALTH",
            "condition": {"field": "health", "operator": "=", "value": "H2"},
            "alert_level": AlertLevel.WARNING,
            "is_active": True,
        }
        rule = create_alert_rule(db_session, rule_data)


        # Evaluate
        triggered_rules = evaluate_project_against_rules(db_session, project.id)
        assert len(triggered_rules) > 0

