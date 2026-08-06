import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from canary import (
    BANDS,
    BASE_INTERVAL_H,
    MAX_INTERVAL_H,
    MIN_INTERVAL_H,
    evaluate_probe,
    near_band_edge,
    next_interval_hours,
)


class CanaryBandsTest(unittest.TestCase):
    def test_healthy_warm_resume_passes(self):
        m = {"cost": 0.0045, "cache_read": 45000, "cache_write": 300}
        self.assertEqual(evaluate_probe("warm_resume", m), [])

    def test_missing_probe_alerts(self):
        self.assertEqual(evaluate_probe("warm_resume", {}),
                         ["warm_resume: probe produced no result"])

    def test_cost_regime_change_alerts(self):
        m = {"cost": 0.30, "cache_read": 45000}
        alerts = evaluate_probe("warm_resume", m)
        self.assertEqual(len(alerts), 1)
        self.assertIn("outside band", alerts[0])

    def test_cold_resume_mechanism_alert(self):
        # In-band cost but no cache read: resume stopped being warm.
        m = {"cost": 0.01, "cache_read": 100, "cache_write": 9000}
        alerts = evaluate_probe("warm_resume", m)
        self.assertTrue(any("no longer warm" in a for a in alerts))

    def test_handoff_without_cache_write_alerts(self):
        # A vanished handoff tax would itself be news (cross-model cache?).
        m = {"cost": 0.05, "cache_read": 30000, "cache_write": 12}
        alerts = evaluate_probe("handoff_tax", m)
        self.assertTrue(any("cache_write" in a for a in alerts))

    def test_fork_must_mint_new_session(self):
        m = {"cost": 0.01, "new_session_id": False}
        alerts = evaluate_probe("fork_warmth", m)
        self.assertTrue(any("new session id" in a for a in alerts))

    def test_integrity_recall_required(self):
        good = {"cost": 0.01, "recalled": True}
        bad = {"cost": 0.01, "recalled": False}
        self.assertEqual(evaluate_probe("integrity", good), [])
        self.assertTrue(any("recall" in a for a in evaluate_probe("integrity", bad)))

    def test_every_band_has_sane_shape(self):
        for name, (lo, hi, _extra) in BANDS.items():
            self.assertLess(lo, hi, name)
            self.assertGreater(lo, 0, name)


class AdaptiveCadenceTest(unittest.TestCase):
    CLEAN = {"alerts": [], "probes": {"warm_resume": {"cost": 0.003}}}

    def test_no_history_uses_base(self):
        self.assertEqual(next_interval_hours([]), BASE_INTERVAL_H)

    def test_alert_investigates_hourly(self):
        history = [self.CLEAN, {"alerts": ["warm_resume: boom"], "probes": {}}]
        self.assertEqual(next_interval_hours(history), MIN_INTERVAL_H)

    def test_near_edge_watches_six_hourly(self):
        # warm_resume band is [0.0008, 0.02]; 0.019 is within 1.5x of the top.
        edgy = {"alerts": [], "probes": {"warm_resume": {"cost": 0.019}}}
        self.assertTrue(near_band_edge("warm_resume", {"cost": 0.019}))
        self.assertEqual(next_interval_hours([edgy]), 6.0)

    def test_healthy_mid_band_is_not_edgy(self):
        self.assertFalse(near_band_edge("warm_resume", {"cost": 0.003}))

    def test_clean_week_stretches_to_cap(self):
        self.assertEqual(next_interval_hours([self.CLEAN] * 7), MAX_INTERVAL_H)

    def test_short_clean_streak_stays_at_base(self):
        self.assertEqual(next_interval_hours([self.CLEAN] * 3), BASE_INTERVAL_H)

    def test_alert_resets_the_streak(self):
        history = [self.CLEAN] * 6 + [{"alerts": ["x"], "probes": {}}] + [self.CLEAN] * 3
        self.assertEqual(next_interval_hours(history), BASE_INTERVAL_H)


if __name__ == "__main__":
    unittest.main()
