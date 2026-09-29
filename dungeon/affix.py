"""副本词缀与秘境罗盘系统 - 含9个bug"""
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
    trigger_phase: int = 0  # 0=全程

class AffixSystem:
    def __init__(self, seed=42):
        self.rng = random.Random(seed)
        self.affix_pool: dict[str, Affix] = {}
        self.locked_affixes: list[str] = []  # bug3: 只能锁1个

    def generate_affixes(self, level: int, count: int) -> list[Affix]:
        # bug1: 不检测冲突
        all_affixes = list(self.affix_pool.values())
        return self.rng.sample(all_affixes, min(count, len(all_affixes)))

    def get_affix_strength(self, affix: Affix, level: int) -> float:
        # bug2: 不随层数增长
        return 1.0

    def lock_affix(self, affix_id: str) -> bool:
        # bug3: 只能锁1个
        if len(self.locked_affixes) >= 1:
            return False
        self.locked_affixes.append(affix_id)
        return True

    def calculate_combined_effect(self, affixes: list[Affix]) -> dict:
        # bug4: 线性叠加无递减
        result = {}
        for a in affixes:
            for k, v in a.effect.items():
                result[k] = result.get(k, 0) + v
        return result

    def get_negative_weight(self) -> float:
        # bug5: 正负权重一样
        return 1.0

    def get_trigger_phase(self, affix: Affix, boss_hp_pct: float) -> bool:
        # bug6: 全程生效
        return True

    def get_duplicate_limit(self) -> int:
        # bug7: 可重复
        return 999

    def get_reward_multiplier(self, affixes: list[Affix]) -> float:
        # bug8: 奖励不匹配难度
        return 1.0

    def reroll_cost(self) -> int:
        # bug9: 重置不消耗
        return 0
