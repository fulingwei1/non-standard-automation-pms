import pytest
from pydantic import ValidationError

from app.schemas.culture_wall_config import (
    ContentTypeConfig,
    CultureWallConfigCreate,
    CultureWallConfigResponse,
    CultureWallConfigUpdate,
    PlaySettings,
)


def test_content_type_and_play_settings_validation():
    content = ContentTypeConfig()
    settings = PlaySettings()

    assert content.enabled is True
    assert content.max_count == 10
    assert content.priority == 0
    assert settings.auto_play is True
    assert settings.interval == 5000
    assert settings.show_controls is True
    assert settings.show_indicators is True

    with pytest.raises(ValidationError):
        ContentTypeConfig(max_count=0)

    with pytest.raises(ValidationError):
        PlaySettings(interval=999)


def test_culture_wall_config_models():
    create = CultureWallConfigCreate(config_name="大厅大屏")
    update = CultureWallConfigUpdate(config_name="大厅大屏-新版", is_default=True)
    response = CultureWallConfigResponse(
        id=1,
        config_name="大厅大屏",
        created_by=7,
        created_at="2026-04-14T03:40:00",
        updated_at="2026-04-14T03:45:00",
    )

    assert create.is_enabled is True
    assert create.is_default is False
    assert create.visible_roles == []
    assert create.play_settings.interval == 5000
    assert set(create.content_types.keys()) == {
        "STRATEGY",
        "CULTURE",
        "IMPORTANT",
        "NOTICE",
        "REWARD",
        "PERSONAL_GOAL",
        "NOTIFICATION",
    }
    assert create.content_types["PERSONAL_GOAL"].max_count == 5
    assert update.is_default is True
    assert response.id == 1
