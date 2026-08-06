import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest
from unittest import mock
from unittest.mock import AsyncMock

import activities
from shared import PushBranchInput, UpdateBranchInput


class UpdateBranchTests(unittest.IsolatedAsyncioTestCase):
    async def test_clean_update_pushes_and_returns_updated(self):
        # clone, config, config, checkout, merge, push — all succeed.
        seq = [(0, "")] * 6
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(activities, "_git", new=AsyncMock(side_effect=seq)):
            r = await activities.update_pr_branch(UpdateBranchInput(repo="o/r", branch="claude/issue-1", number=1))
        self.assertTrue(r.updated)
        self.assertFalse(r.conflict)

    async def test_content_conflict_aborts_and_flags(self):
        # clone, config, config, checkout ok; merge conflicts; abort ok.
        seq = [(0, ""), (0, ""), (0, ""), (0, ""), (1, "CONFLICT (content)"), (0, "")]
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(activities, "_git", new=AsyncMock(side_effect=seq)):
            r = await activities.update_pr_branch(UpdateBranchInput(repo="o/r", branch="claude/issue-1", number=1))
        self.assertFalse(r.updated)
        self.assertTrue(r.conflict)

    async def test_no_token_is_noop(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            r = await activities.update_pr_branch(UpdateBranchInput(repo="o/r", branch="b", number=1))
        self.assertFalse(r.updated)
        self.assertFalse(r.conflict)


class PushBranchTests(unittest.IsolatedAsyncioTestCase):
    async def test_commits_leftover_changes_then_pushes(self):
        # add, status (dirty), commit, push — all succeed.
        seq = [(0, ""), (0, " M backend/app.py"), (0, ""), (0, "")]
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(activities.Path, "write_text", return_value=None), \
             mock.patch.object(activities, "_git", new=AsyncMock(side_effect=seq)) as git:
            r = await activities.push_branch(PushBranchInput(repo="o/r", branch="claude/issue-1", work_dir="/tmp/x"))
        self.assertTrue(r.pushed)
        # last git call is the push to the branch.
        self.assertEqual(git.call_args_list[-1].args[0][0], "push")
        self.assertIn("HEAD:claude/issue-1", git.call_args_list[-1].args[0])

    async def test_clean_merge_commit_skips_commit_and_pushes(self):
        # add, status (clean) -> no commit; push succeeds. Only 3 git calls.
        seq = [(0, ""), (0, ""), (0, "")]
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "tok"}), \
             mock.patch.object(activities.Path, "write_text", return_value=None), \
             mock.patch.object(activities, "_git", new=AsyncMock(side_effect=seq)) as git:
            r = await activities.push_branch(PushBranchInput(repo="o/r", branch="b", work_dir="/tmp/x"))
        self.assertTrue(r.pushed)
        self.assertEqual(git.await_count, 3)  # add, status, push — no commit

    async def test_no_token_is_noop(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            r = await activities.push_branch(PushBranchInput(repo="o/r", branch="b", work_dir="/tmp/x"))
        self.assertFalse(r.pushed)


if __name__ == "__main__":
    unittest.main()
