"""副本词缀与秘境罗盘系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dungeon.affix import AffixSystem, Affix

class TestConflictDetection:
    def test_conflicting_affixes_not_generated_together(self):
        af = AffixSystem()
        af.affix_pool = {
            "a1": Affix("a1", "hp_up", "positive", {"hp": 2}, conflicts=["a2"]),
            "a2": Affix("a2", "hp_down", "negative", {"hp": -2}, conflicts=["a1"]),
        }
        result = af.generate_affixes(10, 2)
        ids = [a.aid for a in result]
        assert not ("a1" in ids and "a2" in ids)  # bug1: 可能同时出现

class TestStrengthScaling:
    def test_affix_strength_scales_with_level(self):
        af = AffixSystem()
        affix = Affix("a1", "dmg", "negative", {"dmg": 10})
        s1 = af.get_affix_strength(affix, 1)
        s100 = af.get_affix_strength(affix, 100)
        assert s100 > s1  # bug2: 都是1.0

class TestMultipleLocks:
    def test_can_lock_multiple_affixes(self):
        af = AffixSystem()
        assert af.lock_affix("a1") == True
        assert af.lock_affix("a2") == True  # bug3: 只能锁1个
        assert af.lock_affix("a3") == True

class TestDiminishingReturns:
    def test_same_effect_has_diminishing_returns(self):
        af = AffixSystem()
        affixes = [Affix(f"a{i}", "dmg", "positive", {"dmg": 10}) for i in range(10)]
        result = af.calculate_combined_effect(affixes)
        assert result["dmg"] < 100  # bug4: 线性=100

class TestNegativeWeight:
    def test_negative_affixes_have_higher_weight(self):
        af = AffixSystem()
        assert af.get_negative_weight() > 1.0  # bug5: 1.0

class TestPhaseTrigger:
    def test_affix_triggers_at_specific_phase(self):
        af = AffixSystem()
        affix = Affix("a1", "enrage", "negative", trigger_phase=30)
        assert af.get_trigger_phase(affix, 50) == False  # bug6: 全程True
        assert af.get_trigger_phase(affix, 25) == True

class TestDuplicateLimit:
    def test_same_affix_cannot_repeat(self):
        af = AffixSystem()
        assert af.get_duplicate_limit() == 1  # bug7: 999

class TestRewardByDifficulty:
    def test_harder_affixes_give_better_reward(self):
        af = AffixSystem()
        easy = [Affix("a1", "easy", "positive", {"dmg": 1})]
        hard = [Affix("a2", "hard", "negative", {"dmg": -100}), Affix("a3", "hard2", "negative", {"hp": -100})]
        r_easy = af.get_reward_multiplier(easy)
        r_hard = af.get_reward_multiplier(hard)
        assert r_hard > r_easy  # bug8: 都是1.0

class TestRerollCost:
    def test_reroll_costs_resources(self):
        af = AffixSystem()
        assert af.reroll_cost() > 0  # bug9: 0
