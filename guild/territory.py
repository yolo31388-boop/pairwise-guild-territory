"""帮派领地与建设系统 - 含9个bug"""
from dataclasses import dataclass, field

class TerritorySystem:
    def __init__(self):
        self.buildings: dict[str, int] = {}  # bug1: 无数量限制
        self.building_times: dict[str, float] = {}  # bug2: 瞬时
        self.production: dict[str, float] = {}  # bug3: 固定产出
        self.defense: dict = {}  # bug4: 无防御
        self.war_prep: float = 0  # bug5: 无准备期
        self.tech_tree: dict = {}  # bug6: 无前置
        self.npc_ai: bool = False  # bug7: 无AI
        self.territory_limit: int = 999  # bug9: 无范围限制

    def get_building_limit(self, building_type: str, territory_level: int) -> int:
        # bug1: 无限制
        return 999

    def get_building_time(self, building_type: str, level: int) -> float:
        # bug2: 瞬时
        return 0.0

    def get_production(self, building_type: str, level: int) -> float:
        # bug3: 固定
        return 10.0

    def get_defense_mechanism(self) -> dict:
        # bug4: 无防御
        return {}

    def get_war_preparation_time(self) -> float:
        # bug5: 无准备期
        return 0.0

    def has_tech_prerequisite(self, tech_id: str, researched: list) -> bool:
        # bug6: 无前置
        return True

    def has_npc_patrol(self) -> bool:
        # bug7: 无AI
        return False

    def get_dynamic_tasks(self, guild_level: int) -> list:
        # bug8: 固定任务
        return ["kill_10_monsters"]

    def get_territory_expansion_limit(self) -> int:
        # bug9: 无限制
        return 999
