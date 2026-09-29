"""帮派领地与建设系统"""
from dataclasses import dataclass, field

# 建筑配置: 每级建造时间(秒)、资源消耗、每小时产出(资源类型, 数量)
BUILDING_CONFIG = {
    "barracks": {"base_time": 1800.0, "base_cost": {"gold": 500, "wood": 300},
                 "production": ("troops", 5.0), "max_per_level": 2},
    "mine": {"base_time": 1200.0, "base_cost": {"gold": 300, "wood": 200},
             "production": ("gold", 20.0), "max_per_level": 3},
    "farm": {"base_time": 900.0, "base_cost": {"gold": 200, "wood": 150},
             "production": ("food", 30.0), "max_per_level": 3},
    "wall": {"base_time": 2400.0, "base_cost": {"gold": 400, "stone": 500},
             "production": ("defense", 0.0), "max_per_level": 1},
    "watchtower": {"base_time": 1500.0, "base_cost": {"gold": 350, "wood": 250},
                   "production": ("defense", 10.0), "max_per_level": 2},
}

# 科技前置依赖树
TECH_TREE = {
    "basic_training": {"requires": [], "time": 600.0},
    "advanced_training": {"requires": ["basic_training"], "time": 1800.0},
    "improved_mining": {"requires": ["basic_training"], "time": 1200.0},
    "fortification": {"requires": ["advanced_training"], "time": 3600.0},
    "ultimate_tech": {"requires": ["fortification", "improved_mining"], "time": 7200.0},
}

# 领地战争默认准备期(秒)与战斗时间窗(秒)
WAR_PREPARATION_TIME = 12 * 3600.0
WAR_BATTLE_WINDOW = 2 * 3600.0

# 领地最大范围(格)
TERRITORY_MAX_RANGE = 64
# 扩张消耗
EXPANSION_COST = {"territory_token": 1, "gold": 1000}


@dataclass
class Building:
    building_type: str
    level: int = 1
    finish_time: float = 0.0  # 升级完成时间戳, 0 表示已完工


class TerritorySystem:
    def __init__(self):
        self.level: int = 1
        self.buildings: list[Building] = []
        self.researched: list[str] = []
        self.defense = {
            "walls": {"level": 1, "hp": 1000},
            "towers": {"count": 1, "damage": 50},
            "breached": False,
        }
        self.war_prep: float = WAR_PREPARATION_TIME
        self.war_battle_window: float = WAR_BATTLE_WINDOW
        self.npc_ai: bool = True
        self.territory_range: int = 4
        self.territory_limit: int = TERRITORY_MAX_RANGE

    # bug1: 建筑数量限制, 随领地等级提升, 同类建筑有上限
    def get_building_limit(self, building_type: str, territory_level: int) -> int:
        cfg = BUILDING_CONFIG.get(building_type, {"max_per_level": 1})
        return cfg["max_per_level"] * max(1, territory_level)

    # bug2: 建筑升级有时间和资源消耗, 高级建筑耗时数小时
    def get_building_time(self, building_type: str, level: int) -> float:
        cfg = BUILDING_CONFIG.get(building_type, {"base_time": 600.0})
        return cfg["base_time"] * (2.0 ** max(0, level - 1))

    def get_building_cost(self, building_type: str, level: int) -> dict:
        cfg = BUILDING_CONFIG.get(building_type, {"base_cost": {"gold": 100}})
        return {res: int(amount * (1.5 ** max(0, level - 1)))
                for res, amount in cfg["base_cost"].items()}

    # bug3: 资源产出按建筑类型和等级区分
    def get_production(self, building_type: str, level: int) -> float:
        cfg = BUILDING_CONFIG.get(building_type)
        if cfg is None:
            return 0.0
        _, rate = cfg["production"]
        return rate * max(1, level)

    def get_production_resource(self, building_type: str) -> str:
        cfg = BUILDING_CONFIG.get(building_type)
        return cfg["production"][0] if cfg else ""

    # bug4: 防御塔 + 城墙, 需攻破才能进入
    def get_defense_mechanism(self) -> dict:
        return {
            "walls": dict(self.defense["walls"]),
            "towers": dict(self.defense["towers"]),
            "requires_breach": True,
            "breached": self.defense["breached"],
        }

    def can_enter(self) -> bool:
        return self.defense["breached"]

    # bug5: 领地战争有准备期与战斗时间窗
    def get_war_preparation_time(self) -> float:
        return self.war_prep

    def get_war_battle_window(self) -> float:
        return self.war_battle_window

    # bug6: 科技前置依赖树
    def has_tech_prerequisite(self, tech_id: str, researched: list) -> bool:
        tech = TECH_TREE.get(tech_id)
        if tech is None:
            return False
        return all(req in researched for req in tech["requires"])

    # bug7: 领地 NPC 巡逻与防御 AI
    def has_npc_patrol(self) -> bool:
        return self.npc_ai

    def get_npc_behavior(self) -> dict:
        return {"patrol": True, "attack_intruders": True, "guard_buildings": True}

    # bug8: 任务按帮派等级和领地类型动态生成
    def get_dynamic_tasks(self, guild_level: int, territory_type: str = "plains") -> list:
        tasks = ["daily_patrol"]
        if guild_level >= 3:
            tasks.append(f"gather_{territory_type}_resources")
        if guild_level >= 5:
            tasks.append("defend_territory")
        if guild_level >= 8:
            tasks.append("elite_expedition")
        if guild_level >= 10:
            tasks.append("territory_war_campaign")
        return tasks

    # bug9: 领地范围限制, 扩张消耗领地令和资源
    def get_territory_expansion_limit(self) -> int:
        return self.territory_limit

    def get_expansion_cost(self, current_range: int) -> dict:
        factor = max(1, current_range // 4)
        return {res: amount * factor for res, amount in EXPANSION_COST.items()}
