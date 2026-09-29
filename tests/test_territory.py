"""帮派领地建设系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from guild.territory import GuildTerritory, Building

class TestPrereq:
    def test_upgrade_requires_prereq(self):
        gt = GuildTerritory()
        gt.buildings["b1"] = Building("b1", "base", level=0)
        gt.buildings["b2"] = Building("b2", "advanced", level=0, prereq=["b1"])
        assert gt.can_upgrade("b2") == False  # bug1: True
        gt.buildings["b1"].level = 3
        assert gt.can_upgrade("b2") == True

class TestResourceDeduction:
    def test_resources_deducted_on_upgrade_start(self):
        gt = GuildTerritory()
        gt.resources = {"gold": 100}
        gt.buildings["b1"] = Building("b1", "base", cost={"gold": 30})
        gt.start_upgrade("b1")
        assert gt.resources["gold"] == 70  # bug2: 还是100

class TestEffectRequiresBuilding:
    def test_unbuilt_building_no_effect(self):
        gt = GuildTerritory()
        gt.buildings["b1"] = Building("b1", "base", level=0, effect={"atk": 10})
        effect = gt.get_building_effect("b1")
        assert effect == {}  # bug3: 返回atk:10

class TestDurability:
    def test_building_takes_damage(self):
        gt = GuildTerritory()
        gt.buildings["b1"] = Building("b1", "wall", durability=100)
        gt.take_damage("b1", 30)
        assert gt.buildings["b1"].durability < 100  # bug4: 不变

class TestQueueLimit:
    def test_upgrade_queue_has_limit(self):
        gt = GuildTerritory()
        assert gt.get_queue_limit() < 10  # bug5: 999

class TestCompletionNotification:
    def test_upgrade_complete_triggers_notification(self):
        gt = GuildTerritory()
        gt.buildings["b1"] = Building("b1", "base")
        gt.notify_on_complete("b1")
        assert hasattr(gt, "notifications") and len(gt.notifications) > 0  # bug6: 无

class TestResourceCap:
    def test_resources_have_storage_cap(self):
        gt = GuildTerritory()
        cap = gt.get_resource_cap("gold")
        assert cap < 100000  # bug7: 999999

class TestArchive:
    def test_disband_archives_territory(self):
        gt = GuildTerritory()
        gt.buildings["b1"] = Building("b1", "base", level=5)
        gt.archive_on_disband("g1")
        assert "g1" in gt.archive  # bug8: 空
