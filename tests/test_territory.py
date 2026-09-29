"""帮派领地与建设系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from guild.territory import TerritorySystem

class TestBuildingLimit:
    def test_building_has_count_limit(self):
        ts = TerritorySystem()
        limit = ts.get_building_limit("barracks", 1)
        assert limit < 10

class TestBuildingTime:
    def test_building_takes_time(self):
        ts = TerritorySystem()
        t = ts.get_building_time("barracks", 1)
        assert t > 0

class TestProduction:
    def test_different_buildings_different_production(self):
        ts = TerritorySystem()
        p1 = ts.get_production("mine", 1)
        p2 = ts.get_production("farm", 1)
        assert p1 != p2

class TestDefense:
    def test_territory_has_defense(self):
        ts = TerritorySystem()
        d = ts.get_defense_mechanism()
        assert d != {}

class TestWarPrep:
    def test_territory_war_has_preparation(self):
        ts = TerritorySystem()
        t = ts.get_war_preparation_time()
        assert t > 0

class TestTechPrerequisite:
    def test_advanced_tech_needs_prerequisite(self):
        ts = TerritorySystem()
        assert ts.has_tech_prerequisite("ultimate_tech", []) == False

class TestNPCAI:
    def test_territory_has_npc_patrol(self):
        ts = TerritorySystem()
        assert ts.has_npc_patrol() == True

class TestDynamicTasks:
    def test_tasks_vary_by_guild_level(self):
        ts = TerritorySystem()
        t1 = ts.get_dynamic_tasks(1)
        t2 = ts.get_dynamic_tasks(10)
        assert t1 != t2

class TestExpansionLimit:
    def test_territory_has_expansion_limit(self):
        ts = TerritorySystem()
        limit = ts.get_territory_expansion_limit()
        assert limit < 100
