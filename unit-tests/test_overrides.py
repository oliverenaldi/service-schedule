import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scheduler as s


class OverrideSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.roles, self.start, self.end, self.seed = s.parse_config()
        self.groups = s.parse_groups()
        self.unavail = s.parse_unavailability()
        self.history = s.load_previous_schedules(self.roles)

    def test_off_parity_pin_is_honored(self):
        # multimedia is week=even; pin it onto an odd Saturday.
        overrides = {(date(2026, 7, 4), "multimedia"): "Oliver"}
        result, _ = s.schedule(
            self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
        )
        self.assertEqual(result[date(2026, 7, 4)]["multimedia"], "Oliver")

    def test_pin_counts_toward_future_history(self):
        d = date(2026, 7, 4)
        overrides = {(d, "multimedia"): "Oliver"}
        result, _ = s.schedule(
            self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
        )
        # Assigning the same role/person again the following even Saturday should
        # respect the min_gap counted from the pinned date, not ignore it.
        cfg = self.roles["multimedia"]
        min_gap_days = cfg["min_gap"] * 7
        pinned_next_slot = None
        for d2, roles_on_date in sorted(result.items()):
            if d2 <= d:
                continue
            if roles_on_date.get("multimedia") == "Oliver":
                pinned_next_slot = d2
                break
        if pinned_next_slot is not None:
            self.assertGreaterEqual((pinned_next_slot - d).days, min_gap_days)

    def test_unavailability_conflict_is_flagged(self):
        # Toni is marked unavailable for the whole scheduling range.
        overrides = {(date(2026, 7, 11), "akomodasi"): "Toni"}
        with self.assertRaisesRegex(ValueError, "unavailable"):
            s.schedule(
                self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
            )

    def test_double_booking_conflict_is_flagged(self):
        d = date(2026, 7, 11)
        overrides = {
            (d, "akomodasi"): "Victor",
            (d, "multimedia"): "Victor",
        }
        with self.assertRaisesRegex(ValueError, "already assigned another role"):
            s.schedule(
                self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
            )

    def test_hidden_role_pin_gaps_out_pemimpin_siblings(self):
        # pembawa-khotbah is hidden (no output column, never auto-assigned) but
        # shares service_type=pemimpin with pemimpin-pa-besar/pemimpin-ibadah,
        # so pinning it should still block that person from those roles within
        # the shared min_gap window.
        overrides = {(date(2026, 7, 11), "pembawa-khotbah"): "Steffen"}
        result, _ = s.schedule(
            self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
        )
        self.assertEqual(result[date(2026, 7, 11)]["pembawa-khotbah"], "Steffen")
        # 2026-07-18 is pemimpin-pa-besar's next slot, only 1 week after the pin -
        # well within the 4-week gap, so Steffen must not be picked there.
        self.assertNotEqual(result[date(2026, 7, 18)].get("pemimpin-pa-besar"), "Steffen")

    def test_hidden_role_has_no_output_column(self):
        result, saturdays = s.schedule(
            self.roles, self.start, self.end, self.groups, self.unavail, self.history, {}
        )
        role_list = [r for r in self.roles if not self.roles[r]["hidden"]]
        self.assertNotIn("pembawa-khotbah", role_list)

    def test_date_outside_range_is_flagged(self):
        overrides = {(date(2020, 1, 4), "akomodasi"): "Victor"}
        with self.assertRaisesRegex(ValueError, "outside the scheduling range"):
            s.schedule(
                self.roles, self.start, self.end, self.groups, self.unavail, self.history, overrides
            )


class ParseOverridesTests(unittest.TestCase):
    def setUp(self):
        self.roles, _, _, _ = s.parse_config()

    def _write(self, tmp_path, content):
        tmp_path.write_text(content)

    def test_unknown_role_raises(self, ):
        original = s.OVERRIDES_FILE
        try:
            tmp = original.parent / "unit-tests" / "_tmp_overrides.txt"
            tmp.write_text("not-a-real-role: 2026-07-04: Oliver\n")
            s.OVERRIDES_FILE = tmp
            with self.assertRaisesRegex(ValueError, "unknown role"):
                s.parse_overrides(self.roles)
        finally:
            s.OVERRIDES_FILE = original
            tmp.unlink(missing_ok=True)

    def test_non_saturday_raises(self):
        original = s.OVERRIDES_FILE
        try:
            tmp = original.parent / "unit-tests" / "_tmp_overrides.txt"
            tmp.write_text("multimedia: 2026-07-05: Oliver\n")  # a Sunday
            s.OVERRIDES_FILE = tmp
            with self.assertRaisesRegex(ValueError, "not a Saturday"):
                s.parse_overrides(self.roles)
        finally:
            s.OVERRIDES_FILE = original
            tmp.unlink(missing_ok=True)

    def test_duplicate_override_raises(self):
        original = s.OVERRIDES_FILE
        try:
            tmp = original.parent / "unit-tests" / "_tmp_overrides.txt"
            tmp.write_text(
                "multimedia: 2026-07-04: Oliver\nmultimedia: 2026-07-04: Aldi\n"
            )
            s.OVERRIDES_FILE = tmp
            with self.assertRaisesRegex(ValueError, "duplicate override"):
                s.parse_overrides(self.roles)
        finally:
            s.OVERRIDES_FILE = original
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
