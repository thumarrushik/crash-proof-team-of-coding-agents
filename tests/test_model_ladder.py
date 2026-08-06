import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from shared import TaskInput, model_for_chunk


class ModelLadderTest(unittest.TestCase):
    def test_disabled_ladder_keeps_base_model(self):
        inp = TaskInput(task="t", model="haiku")
        for chunk in range(8):
            self.assertEqual(model_for_chunk(inp, chunk), "haiku")

    def test_escalates_at_threshold(self):
        inp = TaskInput(task="t", model="haiku",
                        escalate_model="sonnet", escalate_after_chunks=3)
        self.assertEqual(model_for_chunk(inp, 0), "haiku")
        self.assertEqual(model_for_chunk(inp, 2), "haiku")
        self.assertEqual(model_for_chunk(inp, 3), "sonnet")
        self.assertEqual(model_for_chunk(inp, 7), "sonnet")

    def test_ladder_without_base_model(self):
        # No base model (Claude Code default) still escalates on schedule.
        inp = TaskInput(task="t", escalate_model="sonnet", escalate_after_chunks=1)
        self.assertIsNone(model_for_chunk(inp, 0))
        self.assertEqual(model_for_chunk(inp, 1), "sonnet")


if __name__ == "__main__":
    unittest.main()
