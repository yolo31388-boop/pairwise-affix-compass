"""副本词缀与秘境罗盘系统"""
import random
from dataclasses import dataclass, field

MAX_LOCKS = 3
DUPLICATE_LIMIT = 1
NEGATIVE_WEIGHT = 2.0
POSITIVE_WEIGHT = 0.5
DIMINISH_FACTOR = 0.8
REROLL_ENERGY_COST = 10
MAX_COMPASS_ENERGY = 100
ENERGY_RECOVERY_CAP = 100


@dataclass
class Affix:
    aid: str
    name: str
    type: str  # positive/negative
    effect: dict = field(default_factory=dict)
    conflicts: list = field(default_factory=list)
    weight: float = 1.0
    trigger_phase: int = 0  # 0=全程, 否则为Boss血量百分比阈值


class AffixSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict[str, Affix] = {}
        self.locked_affixes: list[str] = []
        self.compass_energy: int = MAX_COMPASS_ENERGY

    def _conflicts_with(self, affix: Affix, chosen: list[Affix]) -> bool:
        chosen_ids = {a.aid for a in chosen}
        for c in chosen:
            if affix.aid in c.conflicts or c.aid in affix.conflicts:
                return True
        return affix.aid in chosen_ids

    def generate_affixes(self, level: int, count: int) -> list[Affix]:
        # fix1: 冲突检测, 互斥词缀不同时出现; 锁定的词缀保留, 其余随机
        result: list[Affix] = []
        for aid in self.locked_affixes:
            locked = self.affix_pool.get(aid)
            if locked is not None and not self._conflicts_with(locked, result):
                result.append(locked)
        candidates = [a for a in self.affix_pool.values()
                      if not self._conflicts_with(a, result)]
        self.rng.shuffle(candidates)
        for cand in candidates:
            if len(result) >= count:
                break
            if not self._conflicts_with(cand, result):
                result.append(cand)
        return result

    def get_affix_strength(self, affix: Affix, level: int) -> float:
        # fix2: 强度随层数指数增长
        level = max(1, level)
        return 1.05 ** (level - 1)

    def lock_affix(self, affix_id: str) -> bool:
        # fix3: 罗盘支持锁定1-3个词缀
        if affix_id in self.locked_affixes:
            return False
        if len(self.locked_affixes) >= MAX_LOCKS:
            return False
        self.locked_affixes.append(affix_id)
        return True

    def calculate_combined_effect(self, affixes: list[Affix]) -> dict:
        # fix4: 同类效果叠加收益递减
        grouped: dict[str, list[float]] = {}
        for a in affixes:
            for k, v in a.effect.items():
                grouped.setdefault(k, []).append(v)
        result = {}
        for k, values in grouped.items():
            values.sort(key=abs, reverse=True)
            total = 0.0
            for i, v in enumerate(values):
                total += v * (DIMINISH_FACTOR ** i)
            result[k] = total
        return result

    def get_negative_weight(self) -> float:
        # fix5: 负面词缀权重更高
        return NEGATIVE_WEIGHT

    def get_trigger_phase(self, affix: Affix, boss_hp_pct: float) -> bool:
        # fix6: 阶段触发, Boss血量降到阈值以下才激活
        if affix.trigger_phase <= 0:
            return True
        return boss_hp_pct <= affix.trigger_phase

    def get_duplicate_limit(self) -> int:
        # fix7: 同类词缀数量上限
        return DUPLICATE_LIMIT

    def get_reward_multiplier(self, affixes: list[Affix]) -> float:
        # fix8: 奖励按词缀难度总分计算, 高风险高回报
        score = 0.0
        for a in affixes:
            magnitude = sum(abs(v) for v in a.effect.values())
            weight = NEGATIVE_WEIGHT if a.type == "negative" else POSITIVE_WEIGHT
            score += magnitude * weight * a.weight
        return 1.0 + score / 100.0

    def reroll_cost(self) -> int:
        # fix9: 重置消耗罗盘能量
        return REROLL_ENERGY_COST

    def reroll(self, level: int, count: int) -> list[Affix] | None:
        # 能量不足则无法重置; 能量恢复有上限
        cost = self.reroll_cost()
        if self.compass_energy < cost:
            return None
        self.compass_energy -= cost
        return self.generate_affixes(level, count)

    def recover_energy(self, amount: int) -> int:
        self.compass_energy = min(self.compass_energy + amount, ENERGY_RECOVERY_CAP)
        return self.compass_energy
