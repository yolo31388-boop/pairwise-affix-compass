"""副本词缀与秘境罗盘系统"""
import random
from dataclasses import dataclass, field

@dataclass
class Affix:
    aid: str
    name: str
    type: str  # positive/negative
    effect: dict = field(default_factory=dict)
    conflicts: list = field(default_factory=list)
    weight: float = 1.0
    trigger_phase: int = 0  # 0=全程, 否则boss血量百分比低于该值时触发

class AffixSystem:
    MAX_LOCKS = 3          # 罗盘最多锁定3个词缀
    DUPLICATE_LIMIT = 1    # 同类词缀数量上限
    NEGATIVE_WEIGHT = 2.0  # 负面词缀权重
    MAX_ENERGY = 100       # 罗盘能量上限
    REROLL_ENERGY = 20     # 每次重置消耗能量
    ENERGY_REGEN = 5       # 每次生成恢复的能量

    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict[str, Affix] = {}
        self.locked_affixes: list[str] = []
        self.energy = self.MAX_ENERGY

    def _conflicts_with(self, affix: Affix, chosen: list[Affix]) -> bool:
        chosen_ids = {a.aid for a in chosen}
        if affix.aid in chosen_ids:
            return True
        for a in chosen:
            if a.aid in affix.conflicts or affix.aid in a.conflicts:
                return True
        return False

    def generate_affixes(self, level: int, count: int) -> list[Affix]:
        # bug1修复: 冲突检测, 互斥词缀不能同时出现; 锁定词缀保留, 其余随机
        result: list[Affix] = []
        for aid in self.locked_affixes:
            locked = self.affix_pool.get(aid)
            if locked is not None and not self._conflicts_with(locked, result):
                result.append(locked)
        candidates = [a for a in self.affix_pool.values()
                      if not self._conflicts_with(a, result)]
        self.rng.shuffle(candidates)
        for a in candidates:
            if len(result) >= count:
                break
            if not self._conflicts_with(a, result):
                result.append(a)
        self.energy = min(self.MAX_ENERGY, self.energy + self.ENERGY_REGEN)
        return result

    def get_affix_strength(self, affix: Affix, level: int) -> float:
        # bug2修复: 强度随层数指数增长
        level = max(1, level)
        return 1.0 * (1.05 ** (level - 1))

    def lock_affix(self, affix_id: str) -> bool:
        # bug3修复: 支持锁定1-3个词缀
        if affix_id in self.locked_affixes:
            return False
        if len(self.locked_affixes) >= self.MAX_LOCKS:
            return False
        self.locked_affixes.append(affix_id)
        return True

    def unlock_affix(self, affix_id: str) -> bool:
        if affix_id in self.locked_affixes:
            self.locked_affixes.remove(affix_id)
            return True
        return False

    def calculate_combined_effect(self, affixes: list[Affix]) -> dict:
        # bug4修复: 同类效果叠加收益递减 (第n个贡献 v / sqrt(n))
        counts: dict[str, int] = {}
        result: dict[str, float] = {}
        for a in affixes:
            for k, v in a.effect.items():
                counts[k] = counts.get(k, 0) + 1
                result[k] = result.get(k, 0.0) + v / (counts[k] ** 0.5)
        return result

    def get_negative_weight(self) -> float:
        # bug5修复: 负面词缀权重更高
        return self.NEGATIVE_WEIGHT

    def get_trigger_phase(self, affix: Affix, boss_hp_pct: float) -> bool:
        # bug6修复: 阶段触发, boss血量低于阈值才激活; 0=全程
        if affix.trigger_phase <= 0:
            return True
        return boss_hp_pct <= affix.trigger_phase

    def get_duplicate_limit(self) -> int:
        # bug7修复: 同类词缀最多1个
        return self.DUPLICATE_LIMIT

    def get_reward_multiplier(self, affixes: list[Affix]) -> float:
        # bug8修复: 按词缀难度总分计算奖励, 负面词缀贡献更高
        score = 0.0
        for a in affixes:
            magnitude = sum(abs(v) for v in a.effect.values())
            if a.type == "negative":
                score += magnitude * self.NEGATIVE_WEIGHT
            else:
                score += magnitude * 0.5
        return 1.0 + score / 100.0

    def reroll_cost(self) -> int:
        # bug9修复: 重置消耗罗盘能量
        return self.REROLL_ENERGY

    def reroll(self, level: int, count: int) -> list[Affix]:
        # 消耗能量重置未锁定词缀, 能量不足返回空
        if self.energy < self.REROLL_ENERGY:
            return []
        self.energy -= self.REROLL_ENERGY
        return self.generate_affixes(level, count)
