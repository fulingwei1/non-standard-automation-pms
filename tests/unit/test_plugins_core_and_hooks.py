import types

import pytest

from app.plugins.core import (
    Plugin,
    PluginConfig,
    PluginManager,
    PluginMetadata,
    PluginStatus,
    get_plugin_manager,
)
from app.plugins.hooks import (
    EventContext,
    EventType,
    HookManager,
    SalesEvents,
    SalesFilters,
    get_hook_manager,
    hook,
)


class DemoPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.loaded = False
        self.enabled_called = False
        self.disabled_called = False
        self.unloaded_called = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="demo",
            version="1.0.0",
            description="demo plugin",
            author="tester",
        )

    def on_load(self) -> None:
        self.loaded = True

    def on_enable(self) -> None:
        self.enabled_called = True

    def on_disable(self) -> None:
        self.disabled_called = True

    def on_unload(self) -> None:
        self.unloaded_called = True


class DependentPlugin(DemoPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="dependent",
            version="1.0.0",
            dependencies=["demo"],
        )


class BrokenLoadPlugin(DemoPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="broken_load", version="1.0.0")

    def on_load(self) -> None:
        raise RuntimeError("load boom")


class BrokenEnablePlugin(DemoPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="broken_enable", version="1.0.0")

    def on_enable(self) -> None:
        raise RuntimeError("enable boom")


class BrokenDisablePlugin(DemoPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="broken_disable", version="1.0.0")

    def on_disable(self) -> None:
        raise RuntimeError("disable boom")


class BrokenUnloadPlugin(DemoPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="broken_unload", version="1.0.0")

    def on_unload(self) -> None:
        raise RuntimeError("unload boom")


def test_plugin_base_properties_and_settings():
    plugin = DemoPlugin()

    assert plugin.status == PluginStatus.DISCOVERED
    assert plugin.name == "demo"
    assert plugin.version == "1.0.0"
    assert plugin.get_settings() == {}

    plugin.update_settings({"a": 1})
    plugin.hook_manager = "hook-manager"
    plugin.db = "db-session"

    assert plugin.get_settings() == {"a": 1}
    assert plugin.hook_manager == "hook-manager"
    assert plugin.db == "db-session"
    assert "demo" in repr(plugin)


def test_plugin_manager_default_dir_and_set_db(tmp_path):
    manager = PluginManager(plugin_dir=str(tmp_path))
    manager._plugins["demo"] = DemoPlugin()

    manager.set_db("db")

    assert manager.plugin_dir == str(tmp_path)
    assert manager.get_plugin("demo").db == "db"
    assert manager._get_default_plugin_dir().endswith("plugins/installed")


def test_discover_plugins_creates_missing_dir(tmp_path):
    missing = tmp_path / "plugins"
    manager = PluginManager(plugin_dir=str(missing))

    discovered = manager.discover_plugins()

    assert discovered == []
    assert missing.exists()


def test_discover_plugins_filters_and_discovers_valid_plugin(tmp_path, monkeypatch):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "_hidden").mkdir()
    (plugin_dir / "plain_file.py").write_text("x")
    valid = plugin_dir / "demo"
    valid.mkdir()
    (valid / "__init__.py").write_text("# test")
    invalid = plugin_dir / "invalid"
    invalid.mkdir()

    manager = PluginManager(plugin_dir=str(plugin_dir))

    fake_module = types.SimpleNamespace(DemoPlugin=DemoPlugin)
    monkeypatch.setattr("app.plugins.core.importlib.import_module", lambda name: fake_module)

    discovered = manager.discover_plugins()

    assert discovered == ["demo"]
    assert manager._plugin_classes["demo"] is DemoPlugin


def test_discover_plugins_handles_import_error(tmp_path, monkeypatch, caplog):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    broken = plugin_dir / "broken"
    broken.mkdir()
    (broken / "__init__.py").write_text("# test")

    manager = PluginManager(plugin_dir=str(plugin_dir))
    monkeypatch.setattr(
        "app.plugins.core.importlib.import_module",
        lambda name: (_ for _ in ()).throw(RuntimeError("import boom")),
    )

    with caplog.at_level("ERROR"):
        discovered = manager.discover_plugins()

    assert discovered == []
    assert "发现插件 broken 失败" in caplog.text


def test_load_plugin_success_and_duplicate_load():
    manager = PluginManager(plugin_dir="unused")
    manager._plugin_classes["demo"] = DemoPlugin

    plugin = manager.load_plugin("demo")
    plugin_again = manager.load_plugin("demo")

    assert plugin is not None
    assert plugin.loaded is True
    assert plugin.status == PluginStatus.LOADED
    assert plugin.hook_manager is manager.hook_manager
    assert plugin_again is plugin


def test_load_plugin_not_discovered_and_load_failure(caplog):
    manager = PluginManager(plugin_dir="unused")

    with caplog.at_level("ERROR"):
        assert manager.load_plugin("missing") is None

    manager._plugin_classes["broken_load"] = BrokenLoadPlugin
    with caplog.at_level("ERROR"):
        assert manager.load_plugin("broken_load") is None

    assert "未发现" in caplog.text
    assert "加载插件 broken_load 失败" in caplog.text


def test_load_all_enable_disable_unload_and_infos():
    manager = PluginManager(plugin_dir="unused")
    manager._plugin_classes.update({"demo": DemoPlugin, "dependent": DependentPlugin})

    loaded = manager.load_all()
    manager._plugins["dependent"].config.priority = 10
    manager._plugins["demo"].config.priority = 20

    assert set(loaded) == {"demo", "dependent"}
    assert manager.enable_plugin("dependent") is False
    assert manager.enable_plugin("demo") is True
    assert manager.enable_plugin("demo") is True
    assert manager.enable_plugin("dependent") is True
    assert manager.enable_all() == 2

    info = manager.get_plugin_info("demo")
    assert info["name"] == "demo"
    assert manager.get_plugin_info("missing") is None
    assert len(manager.list_plugins()) == 2
    assert manager.get_all_plugins().keys() == manager._plugins.keys()

    assert manager.disable_plugin("demo") is True
    assert manager.disable_plugin("demo") is True
    assert manager.unload_plugin("dependent") is True
    assert manager.get_plugin("dependent") is None


def test_enable_disable_unload_failure_paths_and_missing(caplog):
    manager = PluginManager(plugin_dir="unused")
    manager._plugins["broken_enable"] = BrokenEnablePlugin()
    manager._plugins["broken_disable"] = BrokenDisablePlugin()
    manager._plugins["broken_unload"] = BrokenUnloadPlugin()
    manager._plugins["broken_unload"].status = PluginStatus.ENABLED

    with caplog.at_level("ERROR"):
        assert manager.enable_plugin("missing") is False
        assert manager.disable_plugin("missing") is False
        assert manager.unload_plugin("missing") is False
        assert manager.enable_plugin("broken_enable") is False
        assert manager.disable_plugin("broken_disable") is False
        assert manager.unload_plugin("broken_unload") is False

    assert manager._plugins["broken_enable"].status == PluginStatus.ERROR
    assert "未加载" in caplog.text


def test_get_plugin_manager_singleton(monkeypatch):
    monkeypatch.setattr("app.plugins.core._plugin_manager", None)

    first = get_plugin_manager()
    second = get_plugin_manager()

    assert first is second


def test_hook_manager_register_unregister_and_emit(caplog):
    manager = HookManager()
    seen = []

    def first(ctx: EventContext):
        seen.append(("first", ctx.data))
        return "r1"

    def second(ctx: EventContext):
        ctx.cancel()
        seen.append(("second", ctx.data))
        return "r2"

    def boom(ctx: EventContext):
        raise RuntimeError("boom")

    manager.register("evt", first, priority=20, plugin_name="p1")
    manager.register("evt", second, priority=10, plugin_name="p2")
    manager.register("evt", boom, priority=30)

    with caplog.at_level("ERROR"):
        ctx = manager.emit("evt", {"x": 1}, source="test")

    assert ctx.event_name == "evt"
    assert ctx.data == {"x": 1}
    assert ctx.metadata == {"source": "test"}
    assert ctx.cancelled is True
    assert ctx.results == ["r2"]
    assert seen == [("second", {"x": 1})]
    assert manager.unregister("missing") == 0
    assert manager.unregister("evt", handler=second) == 1
    assert manager.unregister("evt", plugin_name="p1") == 1
    assert manager.unregister("evt") == 1
    assert manager.list_events() == ["evt"]
    assert manager.get_hooks("evt")["evt"] == []


@pytest.mark.asyncio
async def test_hook_manager_emit_async_and_filters():
    manager = HookManager()

    def sync_handler(ctx: EventContext):
        return "sync"

    async def async_handler(ctx: EventContext):
        return "async"

    def async_boom(ctx: EventContext):
        raise RuntimeError("async boom")

    manager.register("evt", sync_handler, event_type=EventType.SYNC)
    manager.register("evt", async_handler, event_type=EventType.ASYNC)
    manager.register("evt", async_boom, event_type=EventType.ASYNC)
    manager.register("flt", lambda value, **ctx: value + 2, event_type=EventType.FILTER)
    manager.register("flt", lambda value, **ctx: None, event_type=EventType.FILTER)
    manager.register("flt", lambda value, **ctx: value * 3, event_type=EventType.FILTER)
    manager.register("flt", lambda ctx: ctx, event_type=EventType.SYNC)

    ctx = await manager.emit_async("evt", 123, actor="tester")
    filtered = manager.apply_filters("flt", 4, actor="tester")

    assert ctx.results == ["sync", "async"]
    assert filtered == 18


def test_hook_manager_decorators_enable_disable_and_plugin_unregistration():
    manager = HookManager()

    @manager.on("decorated", priority=5)
    def decorated(ctx: EventContext):
        return "ok"

    @manager.filter("flt", priority=1)
    def plus_one(value, **ctx):
        return value + 1

    manager.register("decorated", decorated, plugin_name="demo-plugin")
    assert manager.unregister_plugin("demo-plugin") == 1

    manager.disable()
    disabled_ctx = manager.emit("decorated", 1)
    assert disabled_ctx.results == []
    assert manager.apply_filters("flt", 10) == 10
    assert manager.is_enabled() is False

    manager.enable()
    enabled_ctx = manager.emit("decorated", 1)
    assert enabled_ctx.results == ["ok"]
    assert manager.apply_filters("flt", 10) == 11
    assert manager.is_enabled() is True


def test_global_hook_manager_and_constants(monkeypatch):
    monkeypatch.setattr("app.plugins.hooks._hook_manager", None)

    manager = get_hook_manager()

    @hook(SalesEvents.CONTRACT_CREATED)
    def on_created(ctx: EventContext):
        return SalesFilters.QUOTE_AMOUNT

    ctx = manager.emit(SalesEvents.CONTRACT_CREATED, {"id": 1})

    assert get_hook_manager() is manager
    assert ctx.results == [SalesFilters.QUOTE_AMOUNT]
    assert SalesEvents.PAYMENT_RECEIVED == "payment.received"
    assert SalesFilters.WIN_PROBABILITY == "opportunity.win_probability"


def test_plugin_config_defaults():
    config = PluginConfig()
    assert config.enabled is True
    assert config.settings == {}
    assert config.priority == 100
