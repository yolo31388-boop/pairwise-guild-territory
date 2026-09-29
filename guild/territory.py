"""帮派领地建设系统 - 含8个bug"""
from dataclasses import dataclass, field

@dataclass
class Building:
    bid: str
    name: str
    level: int = 0
    max_level: int = 10
    prereq: list = field(default_factory=list)
    cost: dict = field(default_factory=dict)
    durability: float = 100  # bug4: 无耐久
    effect: dict = field(default_factory=dict)
    upgrading: bool = False

class GuildTerritory:
    def __init__(self):
        self.buildings: dict[str, Building] = {}
        self.resources: dict[str, int] = {}
        self.upgrade_queue: list = []
        self.max_queue = 1  # bug5: 队列上限
        self.resource_cap: dict[str, int] = {}  # bug7: 无上限
        self.archive: dict = {}  # bug8: 无归档

    def can_upgrade(self, bid: str) -> bool:
        # bug1: 不检查前置
        return bid in self.buildings

    def start_upgrade(self, bid: str) -> tuple[bool, str]:
        # bug2: 只检查不扣除
        b = self.buildings[bid]
        for res, amt in b.cost.items():
            if self.resources.get(res, 0) < amt:
                return False, "no resources"
        b.upgrading = True
        return True, "started"

    def get_building_effect(self, bid: str) -> dict:
        # bug3: 未建造也生效
        if bid in self.buildings:
            return self.buildings[bid].effect
        return {}

    def take_damage(self, bid: str, dmg: float):
        # bug4: 无耐久
        pass

    def get_queue_limit(self) -> int:
        # bug5: 无上限
        return 999

    def notify_on_complete(self, bid: str):
        # bug6: 无通知
        pass

    def get_resource_cap(self, res: str) -> int:
        # bug7: 无上限
        return 999999

    def archive_on_disband(self, guild_id: str):
        # bug8: 不归档
        pass
