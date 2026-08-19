"""The agent subprocess must never inherit the harness's GitHub credentials.

The deny rules block `git push` and the clone URL is token-scrubbed, but the
worker's own env carries GITHUB_TOKEN for the push/merge activities; agent_env
is the third layer, withholding exactly those keys from the agent launch so
"no agent holds a credential that can change the outside world" is true by
construction.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import unittest

from shared import agent_env


class AgentEnvTest(unittest.TestCase):
    def test_strips_github_credentials(self) -> None:
        base = {"GITHUB_TOKEN": "ghp_secret", "GH_TOKEN": "gho_secret", "PATH": "/usr/bin"}
        env = agent_env(base)
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)

    def test_preserves_everything_the_agent_needs(self) -> None:
        base = {
            "HOME": "/Users/x",            # the transcript store lives under it
            "PATH": "/usr/bin",
            "ANTHROPIC_API_KEY": "sk-a",   # the agent's OWN auth passes through
            "CLAUDE_CODE_OAUTH_TOKEN": "t",
            "HEARTBEAT_THROTTLE_SECONDS": "3",
            "GITHUB_TOKEN": "ghp_secret",
        }
        env = agent_env(base)
        for key in ("HOME", "PATH", "ANTHROPIC_API_KEY",
                    "CLAUDE_CODE_OAUTH_TOKEN", "HEARTBEAT_THROTTLE_SECONDS"):
            self.assertEqual(env[key], base[key])
        self.assertNotIn("GITHUB_TOKEN", env)

    def test_does_not_mutate_the_input(self) -> None:
        base = {"GITHUB_TOKEN": "ghp_secret"}
        agent_env(base)
        self.assertIn("GITHUB_TOKEN", base)


if __name__ == "__main__":
    unittest.main()
