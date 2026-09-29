"""帮派领地与建设系统"""
from dataclasses import dataclass, field


# bug1: 建筑数量限制 —— 按领地等级与建筑类型的上限表
BUILDING_LIMITS: dict[str, list[int]] = {
    # 索引 = 领地等级 - 1
    "barracks": [1, 2, 3, 4, 5],
    "mine": [2, 3, 4, 5, 6],
    "farm": [2, 3, 4, 5, 6],
    "wall": [1, 1, 2, 2, 3],
    "watchtower": [1, 2, 2, 3, 4],
}
DEFAULT_BUILDING_LIMIT = 1

# bug2: 升级耗时（秒），高级建筑需要数小时
BASE_BUILD_TIME = 300.0  # 1级建筑 5 分钟
BUILD_TIME_GROWTH = 2.0  # 每级耗时翻倍，高级建筑达数小时

# bug3: 资源产出按建筑类型与等级区分（每小时）
PRODUCTION_TABLE: dict[str, tuple[str, float]] = {
    "mine": ("gold", 100.0),      # 矿场产金
    "farm": ("food", 150.0),      # 农场产粮
    "barracks": ("troops", 5.0),  # 兵营产兵力
    "sawmill": ("wood", 120.0),
    "quarry": ("stone", 80.0),
}
PRODUCTION_LEVEL_BONUS = 0.5  # 每升一级产出 +50%

# bug5: 领地战争准备期与战斗时间窗（秒）
WAR_PREPARATION_TIME = 12 * 3600.0  # 默认 12 小时准备期
WAR_BATTLE_WINDOW = 2 * 3600.0      # 2 小时战斗时间窗

# bug6: 科技前置依赖树
TECH_PREREQUISITES: dict[str, list[str]] = {
    "basic_forging": [],
    "advanced_forging": ["basic_forging"],
    "basic_defense": [],
    "advanced_defense": ["basic_defense"],
    "ultimate_tech": ["advanced_forging", "advanced_defense"],
}

# bug9: 领地范围限制与扩张消耗
MAX_TERRITORY_RADIUS = 20  # 领地最大范围（格）
EXPANSION_TOKEN_COST = 1   # 每次扩张消耗领地令
EXPANSION_RESOURCE_COST = {"gold": 5000.0, "wood": 2000.0}


@dataclass
class DefenseWorks:
    """bug4: 领地防御 —— 防御塔与城墙，需攻破才能进入"""
    wall_hp: float = 5000.0
    tower_count: int = 2
    tower_attack: float = 50.0

    def to_dict(self) -> dict:
        return {
            "wall_hp": self.wall_hp,
            "tower_count": self.tower_count,
            "tower_attack": self.tower_attack,
            "breach_required": True,
        }


@dataclass
class TerritoryNPC:
    """bug7: 领地NPC —— 巡逻与防御AI，会攻击入侵者"""
    name: str
    patrol_route: list = field(default_factory=list)
    attack: float = 30.0
    aggro_range: float = 10.0

    def on_intruder(self, intruder: str) -> str:
        return f"attack:{intruder}"


class TerritorySystem:
    def __init__(self):
        self.buildings: dict[str, int] = {}
        self.building_times: dict[str, float] = {}
        self.production: dict[str, float] = {}
        self.defense: DefenseWorks = DefenseWorks()
        self.war_prep: float = WAR_PREPARATION_TIME
        self.war_battle_window: float = WAR_BATTLE_WINDOW
        self.tech_tree: dict = dict(TECH_PREREQUISITES)
        self.npc_ai: bool = True
        self.npcs: list[TerritoryNPC] = [
            TerritoryNPC("guard_1", patrol_route=["gate", "plaza", "wall"]),
            TerritoryNPC("guard_2", patrol_route=["wall", "mine", "farm"]),
        ]
        self.territory_limit: int = MAX_TERRITORY_RADIUS

    # bug1: 按领地等级与建筑类型限制数量
    def get_building_limit(self, building_type: str, territory_level: int) -> int:
        limits = BUILDING_LIMITS.get(building_type)
        if limits is None:
            return DEFAULT_BUILDING_LIMIT
        idx = max(0, min(territory_level - 1, len(limits) - 1))
        return limits[idx]

    # bug2: 升级需要时间与资源，高级建筑耗时数小时
    def get_building_time(self, building_type: str, level: int) -> float:
        return BASE_BUILD_TIME * (BUILD_TIME_GROWTH ** max(0, level - 1))

    def get_building_cost(self, building_type: str, level: int) -> dict:
        factor = 2.0 ** max(0, level - 1)
        return {"gold": 500.0 * factor, "wood": 200.0 * factor}

    # bug3: 产出按建筑类型与等级区分
    def get_production(self, building_type: str, level: int) -> float:
        entry = PRODUCTION_TABLE.get(building_type)
        if entry is None:
            return 0.0
        _, base = entry
        return base * (1.0 + PRODUCTION_LEVEL_BONUS * max(0, level - 1))

    def get_production_resource(self, building_type: str) -> str:
        entry = PRODUCTION_TABLE.get(building_type)
        return entry[0] if entry else ""

    # bug4: 防御塔 + 城墙机制
    def get_defense_mechanism(self) -> dict:
        return self.defense.to_dict()

    # bug5: 战争准备期（默认12小时）
    def get_war_preparation_time(self) -> float:
        return self.war_prep

    def get_war_battle_window(self) -> float:
        return self.war_battle_window

    # bug6: 科技前置依赖树
    def has_tech_prerequisite(self, tech_id: str, researched: list) -> bool:
        prereqs = self.tech_tree.get(tech_id)
        if prereqs is None:
            return False
        return all(p in researched for p in prereqs)

    # bug7: NPC 巡逻与防御AI
    def has_npc_patrol(self) -> bool:
        return self.npc_ai and any(npc.patrol_route for npc in self.npcs)

    # bug8: 任务按帮派等级与领地类型动态生成
    def get_dynamic_tasks(self, guild_level: int, territory_type: str = "plains") -> list:
        tasks = ["kill_10_monsters"]
        if guild_level >= 3:
            tasks.append(f"gather_{territory_type}_resources")
        if guild_level >= 5:
            tasks.append("defend_territory_raid")
        if guild_level >= 8:
            tasks.append("capture_enemy_outpost")
        if guild_level >= 10:
            tasks.append("epic_territory_war")
        return tasks

    # bug9: 领地范围限制，扩张消耗领地令与资源
    def get_territory_expansion_limit(self) -> int:
        return self.territory_limit

    def get_expansion_cost(self) -> dict:
        cost = {"territory_token": EXPANSION_TOKEN_COST}
        cost.update(EXPANSION_RESOURCE_COST)
        return cost
