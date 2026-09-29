"""帮派领地建设系统。

修复点：
1. 建筑升级前置依赖递归检查；
2. 升级开始时原子扣除资源，任一步骤失败全额返还；
3. 建筑效果仅对已建造且未损毁的建筑生效；
4. 建筑拥有耐久度与防御力，受击按规则扣耐久；
5. 建设队列有可配置上限，满员需等待或取消；
6. 升级完成触发事件，通知所有在线成员；
7. 资源产出受存储上限约束，超出不再增加并发出提醒；
8. 帮派解散时归档领地数据（可查询），重建得到空领地。
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, asdict
from datetime import datetime

DEFAULT_MAX_QUEUE = 3
DEFAULT_RESOURCE_CAP = 50000


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
    def is_built(self) -> bool:
        return self.level > 0

    @property
    def is_destroyed(self) -> bool:
        return self.durability <= 0


@dataclass
class UpgradeTask:
    bid: str
    cost: dict = field(default_factory=dict)
    started_at: str = ""


class GuildTerritory:
    # 跨实例的归档仓库：解散后重建的新领地仍可查询历史。
    _archive_registry: dict[str, dict] = {}

    def __init__(self, max_queue: int = DEFAULT_MAX_QUEUE,
                 resource_cap: dict[str, int] | None = None):
        self.buildings: dict[str, Building] = {}
        self.resources: dict[str, int] = {}
        self.upgrade_queue: list[UpgradeTask] = []
        self.max_queue = max_queue
        self.resource_cap: dict[str, int] = dict(resource_cap or {})
        self.archive: dict[str, dict] = dict(self._archive_registry)
        self.notifications: list[dict] = []
        self.members: dict[str, bool] = {}
        self.member_notifications: dict[str, list[dict]] = {}

    # ---- 成员在线状态 ----
    def add_member(self, member_id: str, online: bool = False) -> None:
        self.members.setdefault(member_id, online)
        self.member_notifications.setdefault(member_id, [])

    def set_online(self, member_id: str, online: bool) -> None:
        self.add_member(member_id, online)
        self.members[member_id] = online

    def online_members(self) -> list[str]:
        return [mid for mid, online in self.members.items() if online]

    # ---- bug1: 前置依赖递归检查 ----
    def _prereqs_satisfied(self, bid: str, seen: frozenset | None = None) -> bool:
        seen = seen or frozenset()
        if bid not in self.buildings or bid in seen:
            return bid in self.buildings
        building = self.buildings[bid]
        chain = seen | {bid}
        for prereq in building.prereq:
            dep = self.buildings.get(prereq)
            if dep is None or not dep.is_built:
                return False
            if not self._prereqs_satisfied(prereq, chain):
                return False
        return True

    def can_upgrade(self, bid: str) -> bool:
        building = self.buildings.get(bid)
        if building is None:
            return False
        if building.level >= building.max_level or building.upgrading:
            return False
        return self._prereqs_satisfied(bid)

    # ---- bug2: 原子扣除资源，失败全额返还 ----
    def _refund(self, spent: dict[str, int]) -> None:
        for res, amt in spent.items():
            self.resources[res] = self.resources.get(res, 0) + amt

    def start_upgrade(self, bid: str) -> tuple[bool, str]:
        building = self.buildings.get(bid)
        if building is None:
            return False, "building not found"
        if building.upgrading:
            return False, "already upgrading"
        if building.level >= building.max_level:
            return False, "max level reached"
        if not self._prereqs_satisfied(bid):
            return False, "prerequisite not satisfied"
        if len(self.upgrade_queue) >= self.max_queue:
            return False, "upgrade queue is full"

        cost = dict(building.cost)
        for res, amt in cost.items():
            if self.resources.get(res, 0) < amt:
                return False, f"not enough {res}"

        spent: dict[str, int] = {}
        try:
            for res, amt in cost.items():
                self.resources[res] = self.resources.get(res, 0) - amt
                spent[res] = amt
            building.upgrading = True
            self.upgrade_queue.append(
                UpgradeTask(bid=bid, cost=spent,
                            started_at=datetime.now().isoformat(timespec="seconds"))
            )
        except Exception:
            self._refund(spent)
            building.upgrading = False
            raise
        return True, "started"

    def cancel_upgrade(self, bid: str) -> tuple[bool, str]:
        for index, task in enumerate(self.upgrade_queue):
            if task.bid == bid:
                self.upgrade_queue.pop(index)
                self._refund(task.cost)
                building = self.buildings.get(bid)
                if building is not None:
                    building.upgrading = False
                return True, "cancelled"
        return False, "not in queue"

    def complete_upgrade(self, bid: str) -> tuple[bool, str]:
        for index, task in enumerate(self.upgrade_queue):
            if task.bid == bid:
                building = self.buildings[bid]
                self.upgrade_queue.pop(index)
                building.upgrading = False
                building.level += 1
                self.notify_on_complete(bid)
                return True, "completed"
        return False, "not in queue"

    # ---- bug3: 效果只对已建造且未损毁的建筑生效 ----
    def get_building_effect(self, bid: str) -> dict:
        building = self.buildings.get(bid)
        if building is None or not building.is_built or building.is_destroyed:
            return {}
        return dict(building.effect)

    def active_effects(self) -> dict:
        merged: dict = {}
        for bid in self.buildings:
            for key, value in self.get_building_effect(bid).items():
                merged[key] = merged.get(key, 0) + value
        return merged

    # ---- bug4: 耐久度与防御力，受击扣耐久 ----
    def take_damage(self, bid: str, damage: float) -> tuple[bool, str]:
        building = self.buildings.get(bid)
        if building is None:
            return False, "building not found"
        if building.is_destroyed:
            return False, "building already destroyed"
        mitigated = max(0.0, damage - building.defense)
        building.durability = max(0.0, building.durability - mitigated)
        if building.is_destroyed:
            return True, "destroyed"
        return True, "damaged"

    def repair(self, bid: str, amount: float | None = None) -> tuple[bool, str]:
        building = self.buildings.get(bid)
        if building is None:
            return False, "building not found"
        if amount is None:
            building.durability = building.max_durability
        else:
            building.durability = min(
                building.max_durability, building.durability + amount
            )
        return True, "repaired"

    # ---- bug5: 可配置的建设队列上限 ----
    def get_queue_limit(self) -> int:
        return self.max_queue

    def queue_slots_left(self) -> int:
        return max(0, self.max_queue - len(self.upgrade_queue))

    # ---- bug6: 完成事件通知所有在线成员 ----
    def _push_event(self, event: dict, recipients: list[str]) -> None:
        event = dict(event)
        event["ts"] = datetime.now().isoformat(timespec="seconds")
        event["recipients"] = list(recipients)
        self.notifications.append(event)
        for member_id in recipients:
            self.member_notifications.setdefault(member_id, []).append(
                copy.deepcopy(event)
            )

    def notify_on_complete(self, bid: str) -> tuple[bool, str]:
        building = self.buildings.get(bid)
        if building is None:
            return False, "building not found"
        recipients = self.online_members()
        self._push_event(
            {
                "type": "building_complete",
                "bid": bid,
                "name": building.name,
                "level": building.level,
                "message": f"建筑 {building.name} 已升至 {building.level} 级",
            },
            recipients,
        )
        return True, "notified"

    # ---- bug7: 资源存储上限与爆仓提醒 ----
    def get_resource_cap(self, res: str) -> int:
        return self.resource_cap.get(res, DEFAULT_RESOURCE_CAP)

    def produce_resource(self, res: str, amount: int) -> int:
        """产出资源，超过上限的部分丢弃；发生截断时发出提醒。返回实际增加量。"""
        if amount <= 0:
            return 0
        cap = self.get_resource_cap(res)
        current = self.resources.get(res, 0)
        new_value = min(cap, current + amount)
        gained = new_value - current
        self.resources[res] = new_value
        if new_value < current + amount:
            self._push_event(
                {
                    "type": "resource_cap_reached",
                    "resource": res,
                    "amount": new_value,
                    "cap": cap,
                    "message": f"{res} 已达存储上限 {cap}，超出产出已丢弃",
                },
                self.online_members(),
            )
        return gained

    # ---- bug8: 解散归档，重建为空领地，历史可查 ----
    def archive_on_disband(self, guild_id: str) -> dict:
        snapshot = {
            "guild_id": guild_id,
            "archived_at": datetime.now().isoformat(timespec="seconds"),
            "resources": copy.deepcopy(self.resources),
            "buildings": {
                bid: copy.deepcopy(asdict(building))
                for bid, building in self.buildings.items()
            },
            "queue": [asdict(task) for task in self.upgrade_queue],
        }
        self.archive[guild_id] = copy.deepcopy(snapshot)
        self._archive_registry[guild_id] = copy.deepcopy(snapshot)

        self.buildings.clear()
        self.resources.clear()
        self.upgrade_queue.clear()
        self.members.clear()
        self.member_notifications.clear()
        return snapshot

    @classmethod
    def query_archive(cls, guild_id: str) -> dict | None:
        snapshot = cls._archive_registry.get(guild_id)
        return copy.deepcopy(snapshot) if snapshot is not None else None

    @classmethod
    def rebuild(cls, max_queue: int = DEFAULT_MAX_QUEUE,
                resource_cap: dict[str, int] | None = None) -> "GuildTerritory":
        """解散后重建：返回全新的空领地，历史归档仍可通过 query_archive 查询。"""
        return cls(max_queue=max_queue, resource_cap=resource_cap)
