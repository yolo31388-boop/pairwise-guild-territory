"""帮派领地建设系统"""
from dataclasses import dataclass, field

DEFAULT_QUEUE_LIMIT = 3
DEFAULT_RESOURCE_CAP = 10000


@dataclass
class Building:
    bid: str
    name: str
    level: int = 0
    max_level: int = 10
    prereq: list = field(default_factory=list)
    cost: dict = field(default_factory=dict)
    durability: float = 100
    max_durability: float = 100
    defense: float = 0
    effect: dict = field(default_factory=dict)
    upgrading: bool = False

    @property
    def built(self) -> bool:
        return self.level > 0

    @property
    def damaged(self) -> bool:
        return self.durability <= 0


class GuildTerritory:
    def __init__(self, max_queue: int = DEFAULT_QUEUE_LIMIT):
        self.buildings: dict[str, Building] = {}
        self.resources: dict[str, int] = {}
        self.upgrade_queue: list = []
        self.max_queue = max_queue
        self.resource_cap: dict[str, int] = {}
        self.archive: dict = {}
        self.notifications: list = []

    def _prereqs_satisfied(self, bid: str, _seen: set | None = None) -> bool:
        """递归检查前置依赖：前置建筑必须已建造且其自身前置也满足。"""
        if _seen is None:
            _seen = set()
        if bid in _seen:
            return True  # 循环依赖保护
        _seen.add(bid)
        b = self.buildings.get(bid)
        if b is None:
            return False
        for pre in b.prereq:
            pb = self.buildings.get(pre)
            if pb is None or not pb.built:
                return False
            if not self._prereqs_satisfied(pre, _seen):
                return False
        return True

    def can_upgrade(self, bid: str) -> bool:
        b = self.buildings.get(bid)
        if b is None:
            return False
        if b.upgrading or b.level >= b.max_level:
            return False
        return self._prereqs_satisfied(bid)

    def start_upgrade(self, bid: str) -> tuple[bool, str]:
        b = self.buildings.get(bid)
        if b is None:
            return False, "no such building"
        if not self.can_upgrade(bid):
            return False, "prereq not satisfied or already upgrading"
        if len(self.upgrade_queue) >= self.max_queue:
            return False, "queue full"
        # 原子扣除：任一资源不足则全额返还已扣部分
        deducted = {}
        for res, amt in b.cost.items():
            if self.resources.get(res, 0) < amt:
                for r, a in deducted.items():
                    self.resources[r] = self.resources.get(r, 0) + a
                return False, "no resources"
            self.resources[res] -= amt
            deducted[res] = amt
        b.upgrading = True
        self.upgrade_queue.append(bid)
        return True, "started"

    def cancel_upgrade(self, bid: str) -> tuple[bool, str]:
        """取消升级，全额返还资源。"""
        b = self.buildings.get(bid)
        if b is None or not b.upgrading:
            return False, "not upgrading"
        for res, amt in b.cost.items():
            self.resources[res] = self.resources.get(res, 0) + amt
        b.upgrading = False
        if bid in self.upgrade_queue:
            self.upgrade_queue.remove(bid)
        return True, "cancelled"

    def complete_upgrade(self, bid: str) -> tuple[bool, str]:
        b = self.buildings.get(bid)
        if b is None or not b.upgrading:
            return False, "not upgrading"
        b.upgrading = False
        b.level += 1
        if bid in self.upgrade_queue:
            self.upgrade_queue.remove(bid)
        self.notify_on_complete(bid)
        return True, "completed"

    def get_building_effect(self, bid: str) -> dict:
        # 只对已建造且未损坏的建筑生效
        b = self.buildings.get(bid)
        if b is None or not b.built or b.damaged:
            return {}
        return dict(b.effect)

    def take_damage(self, bid: str, dmg: float):
        b = self.buildings.get(bid)
        if b is None:
            return
        actual = max(0.0, dmg - b.defense)
        b.durability = max(0.0, b.durability - actual)

    def repair(self, bid: str, amount: float):
        b = self.buildings.get(bid)
        if b is None:
            return
        b.durability = min(b.max_durability, b.durability + amount)

    def get_queue_limit(self) -> int:
        return self.max_queue

    def notify_on_complete(self, bid: str):
        b = self.buildings.get(bid)
        name = b.name if b else bid
        self.notifications.append(
            {"type": "upgrade_complete", "bid": bid,
             "message": f"建筑 {name} 升级完成，新功能已解锁"}
        )

    def get_resource_cap(self, res: str) -> int:
        return self.resource_cap.get(res, DEFAULT_RESOURCE_CAP)

    def add_resource(self, res: str, amount: int) -> int:
        """产出入库，超过存储上限不再增加并提醒。返回实际入库数量。"""
        cap = self.get_resource_cap(res)
        cur = self.resources.get(res, 0)
        accepted = max(0, min(amount, cap - cur))
        self.resources[res] = cur + accepted
        if accepted < amount:
            self.notifications.append(
                {"type": "resource_cap", "resource": res,
                 "message": f"资源 {res} 已达存储上限 {cap}，产出溢出"}
            )
        return accepted

    def archive_on_disband(self, guild_id: str):
        """解散时归档领地数据，随后重置为空领地。"""
        self.archive[guild_id] = {
            "buildings": {
                bid: {"name": b.name, "level": b.level,
                      "durability": b.durability}
                for bid, b in self.buildings.items()
            },
            "resources": dict(self.resources),
        }
        self.buildings = {}
        self.resources = {}
        self.upgrade_queue = []
        self.notifications = []

    def get_archive(self, guild_id: str) -> dict:
        return self.archive.get(guild_id, {})
