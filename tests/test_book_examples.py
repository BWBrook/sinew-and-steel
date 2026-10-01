"""Published examples are executable claims against the shared rules core.

Values are read from the current book sources. Expected results come from
the examples, never the historical analytical model or a convenient seed.
"""

from copy import deepcopy
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import _dice
import _pressure
import _rules
import validate_examples


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def section(text, heading):
    """Take a named Markdown section up to its next peer/parent heading."""
    start = re.search(rf"^(#{{1,6}}) {re.escape(heading)}\s*$", text, re.MULTILINE)
    if start is None:
        raise AssertionError(f"missing published example: {heading}")
    end = re.search(rf"^#{{1,{len(start.group(1))}}} ", text[start.end():], re.MULTILINE)
    return text[start.end():start.end() + end.start()] if end else text[start.end():]


class BookExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load(read("manifest.yaml"))
        cls.manual = read(cls.manifest["rules"]["core"]["adventurers_manual"])
        cls.almanac = read(cls.manifest["rules"]["core"]["custodians_almanac"])
        cls.quickstart = read(cls.manifest["rules"]["quickstart"])
        cls.emberfall = read("rules/scenarios/clanfire_emberfall.md")

    def claim(self, pattern, text):
        match = re.search(pattern, text, re.DOTALL)
        self.assertIsNotNone(match, f"published example no longer matches its numerical claim: {pattern}")
        return tuple(int(value) for value in match.groups())

    def opposed(self, attacker, defender, rolls):
        with patch.object(_dice, "roll_d20", side_effect=rolls) as roller:
            result = _dice.resolve_opposed(attacker, defender)
        self.assertEqual(roller.call_count, len(rolls))
        return result

    def test_manual_intellect_thirteen_tradeoff_budget_and_mixed_builds(self):
        example = section(self.manual, "2.5 Worked example (build points + trade-offs)")
        baseline, intellect = self.claim(r"raise INT from (\d+) to (\d+)", example)
        tradeoff, = self.claim(r"Trade-off version:.*?lower your other scores by (\d+) in total, and spend no", example)
        bought, = self.claim(r"Build-point version: spend (\d+) build points", example)
        mixed, reductions = self.claim(r"Mixed version: spend (\d+) build points and lower other scores by (\d+)", example)
        # Concrete distributions realise the book's aggregate reductions.
        cases = [
            ({"MGT": 7, "REF": 7, "INT": intellect, "EMP": baseline, "LCK": baseline}, 0, tradeoff),
            ({"MGT": baseline, "REF": baseline, "INT": intellect, "EMP": baseline, "LCK": baseline}, bought, 0),
            ({"MGT": 8, "REF": baseline, "INT": intellect, "EMP": baseline, "LCK": baseline}, mixed, reductions),
        ]
        for attributes, expected_price, expected_reductions in cases:
            with self.subTest(attributes=attributes):
                self.assertEqual(sum(max(0, baseline - value) for value in attributes.values()), expected_reductions)
                self.assertEqual(_rules.creation_price(attributes, 5), expected_price)

    def test_grak_is_the_same_standard_build_in_manual_quickstart_and_skin(self):
        skin = self.manifest["skins"]["clanfire"]
        parsed = validate_examples.parse_skin_samples(read(skin["file"]), "clanfire", skin)
        self.assertEqual(parsed.errors, [])
        grak = next(sample for sample in parsed.samples if sample.name.startswith("Grak"))
        quick = section(self.quickstart, "4. Example character")
        statline = next(line for line in quick.splitlines() if "MGT" in line and "STM" in line)
        attributes, stamina = validate_examples.parse_statline(statline, skin["attributes"])
        budget, = self.claim(r"Clanfire skin, (\d+) build points", quick)
        self.assertEqual((grak.attributes, grak.stamina), (attributes, stamina))
        self.assertEqual(grak.bought_tags, ("Megafauna tracker",))
        self.assertEqual(grak.price, budget)
        example = section(self.manual, "2.5 Worked example (build points + trade-offs)")
        might, health, raises, reduced_to, refund, tag_cost, total = self.claim(
            r"Might (\d+) and Stamina (\d+) cost (\d+) build points; lowering Spirit and Instinct to (\d+) pays back (\d+);.*?tag costs (\d+)\. That comes to exactly (\d+)", example,
        )
        self.assertEqual((might, health, reduced_to), (attributes["MGT"], stamina, attributes["SPR"]))
        self.assertEqual(attributes["SPR"], attributes["INS"])
        self.assertEqual(raises - refund + tag_cost, total)
        self.assertEqual(grak.price, total)

    def test_almanac_all_three_six_point_builds(self):
        example = section(self.almanac, "C. Sample builds (baseline 10/5)")
        budget, = self.claim(r"Each costs exactly (\d+) build points", example)
        builds = {}
        for line in example.splitlines():
            cells = [cell.strip().replace("*", "") for cell in line.strip("|").split("|")]
            if len(cells) == 7 and all(value.isdigit() for value in cells[1:]):
                builds[cells[0]] = list(map(int, cells[1:]))
        self.assertEqual(set(builds), {"Scholar", "Iron Brute", "Silver-tongue"})
        for name, values in builds.items():
            with self.subTest(name=name):
                self.assertEqual(_rules.creation_price(dict(zip(("MGT", "REF", "INT", "EMP", "LCK"), values[:5])), values[5]), budget)

    def test_manual_margin_against_soak_examples(self):
        example = section(self.manual, "6.2 Armour & soak")
        edge, margin, soak, damage = self.claim(
            r"blade \(edge \+(\d+)\) at margin \+(\d+) against mail \(soak (\d+)\).*?= \*\*(\d+)\*\*", example,
        )
        larger_margin, larger_damage, weak_margin, minimum = self.claim(
            r"At margin \+(\d+) it would have been (\d+)\. A weak jab at margin \+(\d+) still deals the minimum (\d+)", example,
        )
        for wanted_margin, wanted_damage in ((margin, damage), (larger_margin, larger_damage), (weak_margin, minimum)):
            with self.subTest(margin=wanted_margin), patch.object(_dice, "roll_d20", return_value=12 - wanted_margin):
                check = _dice.resolve_check(12)
                self.assertTrue(check["success"])
                self.assertEqual(check["margin"], wanted_margin)
                self.assertEqual(_rules.damage_from_check(check, edge=edge, soak=soak), wanted_damage)

    def test_quickstart_check_and_three_token_nudge(self):
        stat, die, failed_margin, spend, before, after, final_margin = self.claim(
            r"Example \(check \+ nudge\):\* REF (\d+), you roll (\d+): fail \(margin (-?\d+)\)\.\s*Spend (\d+) Luck to nudge (\d+) to (\d+): success \(margin (-?\d+)\)", self.quickstart,
        )
        with patch.object(_dice, "roll_d20", return_value=die):
            check = _dice.resolve_check(stat)
        self.assertEqual((check["success"], check["margin"]), (False, failed_margin))
        self.assertEqual(before, die)
        nudged = _rules.apply_nudge_to_check(check, -spend)
        self.assertEqual((nudged["result"], nudged["success"], nudged["margin"]), (after, True, final_margin))

    def test_quickstart_opposed_spear_deals_two(self):
        attacker, attack_die, attack_margin = self.claim(r"Attacker MGT (\d+) rolls (\d+) \(margin \+(\d+)\)", self.quickstart)
        defender, defence_die, defence_margin = self.claim(r"Defender REF (\d+) rolls (\d+) \(margin \+(\d+)\)", self.quickstart)
        edge, damage = self.claim(r"A spear \(edge \+(\d+)\) against no armour deals (\d+) damage", self.quickstart)
        result = self.opposed(attacker, defender, [attack_die, defence_die])
        self.assertEqual((result["attacker"]["margin"], result["defender"]["margin"]), (attack_margin, defence_margin))
        self.assertEqual(result["outcome"]["winner"], "attacker")
        self.assertEqual(_rules.damage_from_check(result["attacker"], edge=edge, soak=0), damage)

    def test_emberfall_grak_wounds_wolf_then_tarra_drives_it_off(self):
        grak = section(self.emberfall, "Grak lunges")
        attack, defence = self.claim(r"Grak: roll under Might (\d+).*?Wolf: roll under Fleetness (\d+)", grak)
        attack_die, attack_margin, defence_die, defence_margin = self.claim(
            r"Grak rolls (\d+): success, margin \+(\d+).*?Wolf rolls (\d+): fail, margin (-?\d+)", grak,
        )
        damage, health_before, health_after = self.claim(r"= \*\*(\d+)\*\*\. The wolf drops from Stamina (\d+) to (\d+)", grak)
        result = self.opposed(attack, defence, [attack_die, defence_die])
        self.assertEqual((result["attacker"]["margin"], result["defender"]["margin"]), (attack_margin, defence_margin))
        self.assertEqual(result["outcome"]["winner"], "attacker")
        self.assertEqual(_rules.damage_from_check(result["attacker"], edge=1, soak=0), damage)
        self.assertEqual(health_before - damage, health_after)

        tarra = section(self.emberfall, "Tarra turns fire into a weapon")
        attack, defence = self.claim(r"Tarra: roll under Spirit (\d+).*?Wolf: roll under (\d+)", tarra)
        attack_die, attack_margin, defence_die, defence_margin = self.claim(
            r"Tarra rolls (\d+): success, margin \+(\d+).*?Wolf rolls (\d+): success, margin \+(\d+)", tarra,
        )
        result = self.opposed(attack, defence, [attack_die, defence_die])
        self.assertEqual((result["attacker"]["margin"], result["defender"]["margin"]), (attack_margin, defence_margin))
        self.assertEqual(result["outcome"], {"winner": "attacker", "reason": "higher_margin"})

    def test_almanac_shared_fuse_sequence(self):
        skin = self.manifest["skins"]["free_traders_of_the_drift_marches"]
        actors = ["mara.yaml", "holo.yaml"]
        pressure = _pressure.new_pressure(skin, actors)
        start, jump = self.claim(r"Strain stands at (\d+) when a failed jump adds (\d+)", self.almanac)
        _pressure.change(pressure, skin, actors, amount=start, source="earlier strain", category="ambient")
        _pressure.change(pressure, skin, actors, amount=jump, source="failed jump", category="failure", actor=actors[0])
        _, track = _pressure.track_for(pressure)
        self.assertEqual(track["current"], 3)
        self.assertEqual(track["fired_steps"], [2])
        self.assertEqual(set(track["pending"]), set(actors))
        self.assertEqual(len(track["pending"][actors[1]]), 1)

        # Mara's relevant next test spends its penalty even though Advantage
        # cancels it. Paying the step-3 toll with Luck adds no further Strain.
        modifiers = _pressure.modifiers(pressure, skin, actors[0], "SOC", ["risky"], consume=True)
        self.assertEqual(modifiers["active_steps"], [1, 2, 3])
        self.assertEqual(len(modifiers["disadvantage_sources"]), 1)
        self.assertEqual([cost["step"] for cost in modifiers["costs"]], [3])
        with patch.object(_dice, "roll_d20", return_value=9) as roller:
            check = _dice.resolve_check(8, adv=True, dis=bool(modifiers["disadvantage_sources"]))
        roller.assert_called_once()
        self.assertFalse(check["adv"] or check["dis"])
        self.assertEqual(track["pending"][actors[0]], [])

        purged = _pressure.change(pressure, skin, actors, amount=-2, source="shore leave", category="purge")
        self.assertEqual(track["current"], 1)
        self.assertEqual([item["actor"] for item in purged[0]["discarded"]], [actors[1]])
        self.assertEqual(track["pending"][actors[1]], [])
        _pressure.change(pressure, skin, actors, amount=2, source="strain returns", category="ambient")
        modifiers = _pressure.modifiers(pressure, skin, actors[1], "EDU", ["risky"])
        self.assertEqual(modifiers["disadvantage_sources"], [])
        self.assertEqual([cost["step"] for cost in modifiers["costs"]], [3])
        self.assertEqual(track["fired_steps"], [2])

        _pressure.change(pressure, skin, actors, amount=1, source="later risky action toll", category="action_cost", actor=actors[1])
        # Two failed crew checks charge one group gain, with no single tipper.
        events = _pressure.change(pressure, skin, actors, amount=1, source="crew nerve check (two failed)", category="failure")
        self.assertEqual(len(events), 1)
        self.assertEqual(track["current"], 5)
        self.assertIsNone(track["tipper"])
        self.assertTrue(track["crisis_pending"])
        _pressure.change(pressure, skin, actors, amount=1, source="crisis consequence", category="ambient")
        effect = {"description": "next key SOC test has Disadvantage", "duration": "next key SOC test"}
        _pressure.crisis(pressure, skin, actors, target=actors[0], table_result=[3], description="Mutiny spark", effects=[effect])
        self.assertEqual((track["current"], track["cycle"], track["fired_steps"], track["pending"]), (0, 1, [], {}))
        self.assertEqual(len(pressure["crises"]), 1)
        self.assertEqual(pressure["crises"][0]["target"], actors[0])
        self.assertTrue(pressure["effects"][0]["active"])
        self.assertEqual(pressure["effects"][0]["duration"], "next key SOC test")
        _pressure.change(pressure, skin, actors, amount=2, source="new cycle", category="ambient")
        self.assertEqual(track["fired_steps"], [2])
        self.assertTrue(all(track["pending"][actor] for actor in actors))
        self.assertEqual(_pressure.validate_pressure(pressure, skin, actors), [])


class PublishedSampleValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = yaml.safe_load(read("manifest.yaml"))
        cls.skin = cls.manifest["skins"]["clanfire"]
        cls.text = read(cls.skin["file"])

    def test_all_twenty_samples_are_checked_with_free_grants_and_bought_tags(self):
        checked = validate_examples.validate_samples(self.manifest)
        self.assertEqual(checked.errors, [])
        self.assertEqual(len(checked.samples), 20)
        self.assertEqual({sample.skin for sample in checked.samples}, set(self.manifest["skins"]))
        paid_tags = [tag for sample in checked.samples for tag in sample.bought_tags]
        self.assertCountEqual(paid_tags, ["Megafauna tracker", "Streetwise"])
        self.assertEqual(sum(len(sample.free_tags) for sample in checked.samples), 12)

    def test_missing_or_malformed_samples_never_silently_pass(self):
        mutations = {
            "no sample section": self.text.split("## Example clansfolk")[0],
            "missing character": self.text.split("### Tarra the Ember-Singer")[0],
            "missing creation": self.text.replace("Creation: standard budget (6 build points).<br>", "", 1),
            "missing score": self.text.replace("CUN 10 | ", "", 1),
            "out of range": self.text.replace("MGT 12 | FLT 10", "MGT 17 | FLT 10", 1),
        }
        for failure, text in mutations.items():
            with self.subTest(failure=failure):
                self.assertTrue(validate_examples.parse_skin_samples(text, "clanfire", self.skin).errors)
        self.assertTrue(validate_examples.validate_samples({"skins": {}}).errors)

    def test_stated_spending_and_budget_are_both_enforced(self):
        for creation in ("(6 build points; used 5)", "(4 build points; used 6)"):
            with self.subTest(creation=creation):
                text = self.text.replace("(6 build points)", creation, 1)
                self.assertTrue(validate_examples.parse_skin_samples(text, "clanfire", self.skin).errors)

    def test_reductions_above_eight_do_not_buy_a_tag(self):
        text = self.text.replace("MGT 12 | FLT 10 | CUN 10 | SPR 8 | INS 8/8 | STM 7/7", "MGT 16 | FLT 6 | CUN 6 | SPR 6 | INS 8/8 | STM 9/9", 1)
        text = text.replace("(6 build points)", "(12 build points; used 12)", 1)
        parsed = validate_examples.parse_skin_samples(text, "clanfire", self.skin)
        grak = parsed.samples[0]
        self.assertEqual(grak.price, 14)  # 20 raises - cap 8 + 2 bought tag.
        self.assertTrue(any("exceeds budget" in error for error in parsed.errors))

    def test_further_knacks_beyond_the_free_grant_are_bought(self):
        skin = deepcopy(self.manifest["skins"]["whispers_in_the_fog"])
        text = read(skin["file"]).replace("Knack: Occult Scholar.", "Knacks: Occult Scholar; Steady Nerves.", 1)
        parsed = validate_examples.parse_skin_samples(text, "whispers_in_the_fog", skin)
        self.assertEqual(parsed.samples[0].free_tags, ("Occult Scholar",))
        self.assertEqual(parsed.samples[0].bought_tags, ("Steady Nerves",))
        self.assertTrue(any("exceeds budget" in error for error in parsed.errors))


if __name__ == "__main__":
    unittest.main()
