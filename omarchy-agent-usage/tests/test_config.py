"""Tests for the rogarchy-skills config.env reader (env var > config.env > default).
Run: python3 -m unittest discover -s omarchy-agent-usage/tests
Uses a temp XDG_CONFIG_HOME only; never reads the real config file."""
import importlib.util
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL / "scripts"))
import common  # noqa: E402

# dither-data-viz carries its own copy of the reader (skills stay self-contained).
DONUT = SKILL.parent / "dither-data-viz" / "scripts" / "build_donut_card.py"
VARS = ("OMARCHY_USAGE_DATA", "OMARCHY_PATH", "OMARCHY_TASKS_FILE", "XDG_STATE_HOME",
        "ARTIFICIAL_ANALYSIS_API_KEY", "HOME_TEST_VALUE")


def load_donut():
    spec = importlib.util.spec_from_file_location("build_donut_card", DONUT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ConfigReaderBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="rs-config-test-"))
        self.env = mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.tmp)})
        self.env.start()
        for var in VARS:
            os.environ.pop(var, None)          # restored by env.stop()
        self.cfg = self.tmp / "rogarchy-skills" / "config.env"

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, text):
        self.cfg.parent.mkdir(parents=True, exist_ok=True)
        self.cfg.write_text(text, encoding="utf-8")


class TestCommonSetting(ConfigReaderBase):
    def test_config_file_honors_xdg_config_home(self):
        self.assertEqual(common.config_file(), self.cfg)

    def test_missing_file_is_default(self):
        self.assertIsNone(common.setting("OMARCHY_PATH"))
        self.assertEqual(common.omarchy_path(), Path("/usr/share/omarchy"))

    def test_config_wins_over_default(self):
        self.write("# rogarchy-skills config v1\nOMARCHY_PATH=/opt/omarchy\n")
        self.assertEqual(common.omarchy_path(), Path("/opt/omarchy"))
        self.write("OMARCHY_USAGE_DATA=/srv/usage\n")
        self.assertEqual(common.data_dir(create=False), Path("/srv/usage"))

    def test_env_wins_over_config(self):
        self.write("OMARCHY_PATH=/opt/omarchy\n")
        os.environ["OMARCHY_PATH"] = "/env/omarchy"
        self.assertEqual(common.omarchy_path(), Path("/env/omarchy"))

    def test_empty_env_falls_through_to_config(self):
        self.write("OMARCHY_PATH=/opt/omarchy\n")
        os.environ["OMARCHY_PATH"] = ""
        self.assertEqual(common.omarchy_path(), Path("/opt/omarchy"))

    def test_comments_blank_lines_and_last_line_wins(self):
        self.write("# rogarchy-skills config v1\n\n  # OMARCHY_PATH=/commented\n"
                   "OMARCHY_PATH=/first\r\nOTHER=x\nOMARCHY_PATH=/second   \n")
        self.assertEqual(common.setting("OMARCHY_PATH"), "/second")

    def test_empty_value_is_unset(self):
        self.write("OMARCHY_PATH=\n")
        self.assertIsNone(common.setting("OMARCHY_PATH"))

    def test_no_shell_expansion_or_quote_stripping(self):
        self.write('HOME_TEST_VALUE=$HOME/x\nOMARCHY_PATH="/quoted"\nOMARCHY_TASKS_FILE=$(id)\n')
        self.assertEqual(common.setting("HOME_TEST_VALUE"), "$HOME/x")
        self.assertEqual(common.setting("OMARCHY_PATH"), '"/quoted"')
        self.assertEqual(common.setting("OMARCHY_TASKS_FILE"), "$(id)")

    def test_key_must_match_exactly(self):
        self.write("OMARCHY_PATH_X=/nope\n OMARCHY_PATH=/indented\nexport OMARCHY_PATH=/export\n")
        self.assertIsNone(common.setting("OMARCHY_PATH"))

    def test_xdg_state_home_not_read_from_config(self):
        self.write("XDG_STATE_HOME=/from-config\n")
        self.assertEqual(common.data_dir(create=False),
                         Path.home() / ".local/state/omarchy/agents/usage-history")

    def test_api_key_is_env_only(self):
        import cost
        self.write("ARTIFICIAL_ANALYSIS_API_KEY=from-file\n")
        self.assertEqual(cost.api_key(), "")


@unittest.skipUnless(DONUT.is_file(), "dither-data-viz not next to this skill")
class TestDonutSetting(ConfigReaderBase):
    def setUp(self):
        super().setUp()
        self.donut = load_donut()

    def test_default_honors_xdg_state_home(self):
        os.environ["XDG_STATE_HOME"] = str(self.tmp / "state")
        self.assertEqual(self.donut.default_data_dir(),
                         self.tmp / "state" / "omarchy" / "agents" / "usage-history")

    def test_default_without_xdg(self):
        self.assertEqual(self.donut.default_data_dir(),
                         Path.home() / ".local" / "state" / "omarchy" / "agents" / "usage-history")

    def test_config_then_env(self):
        self.write("OMARCHY_USAGE_DATA=/cfg/usage\n")
        self.assertEqual(self.donut.default_data_dir(), Path("/cfg/usage"))
        os.environ["OMARCHY_USAGE_DATA"] = "/env/usage"
        self.assertEqual(self.donut.default_data_dir(), Path("/env/usage"))

    def test_same_parsing_as_common(self):
        text = "# v1\n\nOMARCHY_PATH=$HOME/a\nOMARCHY_PATH=/b \nX=1\n"
        self.write(text)
        self.assertEqual(self.donut.setting("OMARCHY_PATH"), common.setting("OMARCHY_PATH"))


if __name__ == "__main__":
    unittest.main()
