"""Fixture tests for omarchy-agent-usage. Run:
  cd omarchy-agent-usage        # folder skill di repo ini (atau jalankan dari mana saja, path dihitung dari file ini)
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
Never touches real state; network is disabled."""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
FIX = SKILL / "tests" / "fixtures"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL / "scripts"))

_net = None


def setUpModule():
    global _net
    os.environ["TZ"] = "Asia/Jakarta"
    time.tzset()

    def _no_network(*a, **k):
        raise RuntimeError("network disabled in tests")

    _net = mock.patch.object(urllib.request, "urlopen", _no_network)
    _net.start()


def tearDownModule():
    _net.stop()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="oau-test-"))
        self.data = self.tmp / "data"
        (self.data / "snapshots").mkdir(parents=True)
        self.env = mock.patch.dict(os.environ, {
            "OMARCHY_USAGE_DATA": str(self.data),
            "OMARCHY_USAGE_PRICING_CACHE": str(self.tmp / "cache" / "pricing.json"),
            "OMARCHY_USAGE_PRICING_SEED": str(FIX / "pricing_seed.json"),
            "OMARCHY_TASKS_FILE": str(FIX / "tasks.jsonl"),
            "XDG_CONFIG_HOME": str(self.tmp / "config"),   # never read the real config.env
        })
        self.env.start()
        os.environ.pop("ARTIFICIAL_ANALYSIS_API_KEY", None)   # restored by env.stop()
        self.skill_listing = sorted(p.name for p in (SKILL / "scripts").iterdir())

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)
        # nothing may ever be written into the skill's scripts/ dir
        self.assertEqual(self.skill_listing, sorted(p.name for p in (SKILL / "scripts").iterdir()))

    def copy_snapshots(self):
        for p in (FIX / "snapshots").glob("*.json"):
            shutil.copy(p, self.data / "snapshots" / p.name)

    def copy_csv(self):
        shutil.copy(FIX / "daily_by_model.csv", self.data / "daily_by_model.csv")


class TestPhase1(Base):
    def test_merge_latest_wins_and_incomplete_never_replaces_complete(self):
        import common
        self.copy_snapshots()
        snaps = common.load_all_snapshots()
        latest, record_latest, sessions, source = common.merge_snapshots(snaps)
        self.assertEqual(latest["2026-11-10"]["hermes"]["m1"]["tokens"], 20)        # latest wins
        self.assertEqual(latest["2026-11-09"]["codex"]["gpt-6-luna"]["tokens"], 100)  # incomplete B ignored
        self.assertEqual(record_latest["2026-11-10"]["grok"], 500)
        self.assertEqual(record_latest["2026-11-10"]["hermes"], 35)

    def test_distinct_session_counting(self):
        import common, collect
        self.copy_snapshots()
        snaps = common.load_all_snapshots()
        _, _, sessions, _ = common.merge_snapshots(snaps)
        self.assertEqual(sessions["2026-11-10"]["hermes"], 2)   # not 1+1+2 = 4
        self.assertEqual(sessions["2026-11-09"]["codex"], 1)    # v1 path: recomputed from rows
        with redirect_stdout(io.StringIO()):
            collect.build_csvs(snaps)
        import csv
        with open(self.data / "daily.csv") as fh:
            daily = list(csv.DictReader(fh))
        h = [r for r in daily if r["date"] == "2026-11-10" and r["agent"] == "hermes"][0]
        self.assertEqual((h["sessions"], h["tokens"], h["source"]), ("2", "35", "model-rows"))
        g = [r for r in daily if r["agent"] == "grok"][0]
        self.assertEqual((g["source"], g["tokens"]), ("usage-record", "500"))

    def test_corrupt_and_archive_snapshots_skipped(self):
        import common
        self.copy_snapshots()
        (self.data / "snapshots" / "bad.json").write_text("{")
        (self.data / "snapshots" / "archive").mkdir()
        shutil.copy(FIX / "snapshots" / "2026-11-10.json", self.data / "snapshots" / "archive" / "2026-11-10.json")
        err = io.StringIO()
        with redirect_stderr(err):
            snaps = common.load_all_snapshots()
        self.assertEqual([s["today"] for s in snaps], ["2026-11-10", "2026-11-11"])
        self.assertIn("bad.json", err.getvalue())

    def test_atomic_write_leaves_no_temp_files(self):
        import common
        common.atomic_write_text(self.data / "x.txt", "hello")
        self.assertEqual((self.data / "x.txt").read_text(), "hello")
        self.assertEqual([p.name for p in self.data.iterdir() if p.name.endswith(".tmp")], [])

    def test_tasks_dedupe_timezone_and_validation(self):
        import common
        agg, info = common.read_tasks()
        self.assertEqual(info, {"raw": 8, "malformed": 2, "duplicates": 1, "tasks": 5})
        self.assertEqual(agg[("2026-11-10", "hermes")], {"ok": 2, "partial": 1, "fail": 0, "weight": 2.5})
        self.assertEqual(agg[("2026-11-12", "hermes")]["weight"], 1.0)   # 20:00Z -> 03:00 local next day
        self.assertEqual(agg[("2026-11-10", "codex")], {"ok": 0, "partial": 0, "fail": 1, "weight": 0.0})
        self.assertEqual(common.local_date_from_ts("2026-11-18T20:00:00Z"), "2026-11-19")

    def test_tasklog_record_validation_unchanged(self):
        import tasklog
        out = self.tmp / "t.jsonl"
        with mock.patch.dict(os.environ, {"OMARCHY_TASKS_FILE": str(out)}):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(tasklog.main.__call__ if False else 0, 0)
                sys_argv = sys.argv
                try:
                    sys.argv = ["tasklog.py", "record", "--agent", "nobody"]
                    self.assertEqual(tasklog.main(), 1)
                    sys.argv = ["tasklog.py", "record", "--agent", "hermes", "--session", "x"]
                    self.assertEqual(tasklog.main(), 0)
                finally:
                    sys.argv = sys_argv
        self.assertEqual(len(out.read_text().splitlines()), 1)

    def test_build_report_writes_to_data_dir(self):
        import common, collect
        self.copy_snapshots()
        with redirect_stdout(io.StringIO()):
            collect.build_report(common.load_all_snapshots())
        text = (self.data / "report.md").read_text()
        self.assertIn("Data dir", text)
        self.assertIn("hermes", text)

    def test_paths_resolve_from_env_at_call_time(self):
        import common
        self.assertEqual(common.data_dir(), self.data)
        with mock.patch.dict(os.environ, {"OMARCHY_USAGE_DATA": str(self.tmp / "other")}):
            self.assertEqual(common.data_dir(), self.tmp / "other")


def run_main(mod, argv):
    old = sys.argv
    sys.argv = [mod.__name__ + ".py", *argv]
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = mod.main()
    finally:
        sys.argv = old
    return rc, out.getvalue(), err.getvalue()


class TestPhase3(Base):
    def _recs(self):
        import cost
        self.copy_csv()
        with redirect_stderr(io.StringIO()):
            prices, meta = cost.load_prices(offline=True)
        return cost, prices, meta, cost.build_recs(cost.read_rows(), prices)

    def test_free_precedence_before_model_map(self):
        import cost
        prices = {"glm-5-3-flash": {"input": 0.15, "output": 0.5, "cacheHit": 0.03, "cacheWrite": 0}}
        with mock.patch.dict(cost.MODEL_MAP, {"GLM-5.3-flash-free": "glm-5-3-flash"}):
            self.assertEqual(cost.prices_for("GLM-5.3-flash-free", prices)[0], "free")

    def test_costs_successor_cachehit_and_kinds(self):
        cost, prices, meta, recs = self._recs()
        by = {(r["date"], r["agent"], r["model"]): r for r in recs}
        self.assertEqual(meta["mode"], "seed")
        self.assertAlmostEqual(by[("2026-11-10", "claude", "claude-opus-5-5")]["cost"], 0.47)  # cache read @ cacheHit 0.25
        c = by[("2026-11-10", "codex", "gpt-6.1-sol")]
        self.assertEqual((c["kind"], c["label"]), ("paid", "gpt-6-2-sol"))
        self.assertAlmostEqual(c["cost"], 0.21)
        g = by[("2026-11-10", "hermes", "GLM-5.3-flash-free")]
        self.assertEqual(g["kind"], "free")
        self.assertAlmostEqual(g["proxy"], 0.01)
        self.assertEqual(by[("2026-11-10", "hermes", "(unknown)")]["kind"], "tokenless")
        self.assertEqual(by[("2026-11-10", "hermes", "mystery-model")]["kind"], "unknown")
        row = {"inputTokens": 10**6, "outputTokens": 0, "cacheReadInputTokens": 10**6, "cacheCreationInputTokens": 10**6}
        self.assertAlmostEqual(cost.cost_of(row, prices["no-cache-slug"]), 3.25)   # MINOR 4 fallback

    def test_unmapped_rows_surfaced_in_report(self):
        cost, prices, meta, recs = self._recs()
        s = cost.pricing_summary(recs, prices)
        self.assertEqual(s["unpriced_tokens"], 2000)
        self.assertFalse(s["incomplete"])
        self.assertEqual(s["partial_days"], ["2026-11-10"])
        with redirect_stdout(io.StringIO()):
            cost.write_report(recs, prices, meta, s)
        md = (self.data / "cost_report.md").read_text()
        section = md.split("### Tidak terhitung")[1].split("###")[0]
        self.assertIn("mystery-model", section)
        self.assertIn("2,000", section)
        self.assertNotIn("(unknown)", section)
        self.assertIn("GLM-5.3-flash-free", md.split("### Model free")[1])
        self.assertIn("| gpt-6.1-sol | gpt-6-2-sol | gpt-6-1-sol |", md)
        self.assertIn("**Total (hanya token terharga): $0.79**", md)
        self.assertIn("fetched_at", md)
        self.assertIn("Snapshot terbaru", md)

    def test_incomplete_banner(self):
        cost, prices, meta, recs = self._recs()
        for r in recs:
            if r["model"] == "mystery-model":
                r["tokens"] = 10**6
        s = cost.pricing_summary(recs, prices)
        self.assertTrue(s["incomplete"])
        self.assertIn("INCOMPLETE", "\n".join(cost.pricing_sections_md(s)))

    def test_pricing_cache_merge_preserves_retired_slugs(self):
        import cost, common, hashlib
        seed_sha = hashlib.sha256((FIX / "pricing_seed.json").read_bytes()).hexdigest()
        cache = common.pricing_cache_path()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({"meta": {"fetched_at": "2026-11-15T00:00:00+07:00", "mode": "live"},
                                     "prices": {"gpt-6-1-sol": {"input": 2, "output": 10, "cacheHit": 0.1,
                                                                "cacheWrite": None, "stale": False,
                                                                "last_seen": "2026-11-15T00:00:00+07:00"}}}))
        live = {"gpt-6-2-sol": {"input": 2, "output": 10, "cacheHit": 0.1, "cacheWrite": 2.5}}
        with mock.patch.dict(os.environ, {"ARTIFICIAL_ANALYSIS_API_KEY": "test-key"}), \
                mock.patch.object(cost, "fetch_prices", return_value=live), redirect_stderr(io.StringIO()):
            prices, meta = cost.load_prices(offline=False)
        self.assertEqual(meta["mode"], "live")
        self.assertTrue(prices["gpt-6-1-sol"]["stale"])
        self.assertEqual(prices["gpt-6-1-sol"]["last_seen"], "2026-11-15T00:00:00+07:00")
        self.assertFalse(prices["gpt-6-2-sol"]["stale"])
        on_disk = json.loads(cache.read_text())["prices"]
        for slug in ("gpt-6-1-sol", "gpt-6-2-sol", "claude-opus-5-5"):
            self.assertIn(slug, on_disk)
        self.assertEqual(seed_sha, hashlib.sha256((FIX / "pricing_seed.json").read_bytes()).hexdigest())

    # ---- Artificial Analysis Data API (fixture response, no live calls) ----
    def _api_pages(self):
        return json.loads((FIX / "aa_api_response.json").read_text())["pages"]

    def test_parse_api_models_maps_to_price_format(self):
        import cost
        models = [m for pg in self._api_pages() for m in pg["data"]]
        prices = cost.parse_api_models(models)
        self.assertEqual(prices["claude-opus-5-5"],
                         {"input": 1.5, "output": 7, "cacheHit": 0.25, "cacheWrite": 1.9})   # first wins
        self.assertEqual(prices["gpt-6-2-sol"], {"input": 0.75, "output": 3, "cacheHit": None, "cacheWrite": None})
        self.assertNotIn("no-price-model", prices)

    def test_fetch_prices_paginates_and_sends_key_header(self):
        import cost
        pages = self._api_pages()
        seen = []

        class Resp:
            def __init__(self, d): self.d = d
            def read(self): return json.dumps(self.d).encode()

        def fake(req, timeout=0):
            seen.append((req.full_url, req.get_header("X-api-key")))
            return Resp(pages[len(seen) - 1])

        with mock.patch.object(urllib.request, "urlopen", fake):
            prices = cost.fetch_prices("test-key")
        self.assertEqual([u for u, _ in seen], [cost.API_URL + "?page=1", cost.API_URL + "?page=2"])
        self.assertTrue(all(k == "test-key" for _, k in seen))
        self.assertEqual(set(prices), {"claude-opus-5-5", "gpt-6-2-sol"})

    def test_no_key_means_no_network_and_one_hint_line(self):
        import cost
        with mock.patch.object(cost, "fetch_prices", side_effect=AssertionError("network call")):
            err = io.StringIO()
            with redirect_stderr(err):
                prices, meta = cost.load_prices(offline=False)
        self.assertEqual(meta["mode"], "seed")
        hint = [l for l in err.getvalue().splitlines() if "ARTIFICIAL_ANALYSIS_API_KEY" in l]
        self.assertEqual(len(hint), 1)
        self.assertIn("artificialanalysis.ai", hint[0])

    def test_fresh_api_cache_skips_api_call(self):
        import cost, common
        cache = common.pricing_cache_path()
        cache.parent.mkdir(parents=True, exist_ok=True)
        now = cost._now_iso()
        cache.write_text(json.dumps({"meta": {"fetched_at": now, "source": cost.API_URL, "mode": "live"},
                                     "prices": {"claude-opus-5-5": {"input": 1, "output": 2,
                                                                    "cacheHit": None, "cacheWrite": None}}}))
        with mock.patch.dict(os.environ, {"ARTIFICIAL_ANALYSIS_API_KEY": "test-key"}), \
                mock.patch.object(cost, "fetch_prices", side_effect=AssertionError("network call")):
            prices, meta = cost.load_prices(offline=False)
        self.assertEqual(prices["claude-opus-5-5"]["input"], 1)

    def test_free_models_and_proxy_slugs(self):
        import cost
        self.assertEqual(cost.prices_for("glm-4.5-flash", {})[0], "free")       # free, not "unpriced"
        self.assertEqual(cost.PROXY["upstage/solar-pro4:free"], "solar-pro4")   # AA slug has no dash
        self.assertNotIn("glm-4.5-flash", cost.MODEL_MAP)

    def test_attribution_in_report(self):
        cost, prices, meta, recs = self._recs()
        s = cost.pricing_summary(recs, prices)
        with redirect_stdout(io.StringIO()):
            cost.write_report(recs, prices, meta, s)
        text = (self.data / "cost_report.md").read_text()
        self.assertIn("[Source: Artificial Analysis (artificialanalysis.ai)](https://artificialanalysis.ai/)", text)
        self.assertIn("Based on data from Artificial Analysis", text)
        self.assertIn("Created by omarchy-agent-usage, not by Artificial Analysis.", text)
        self.assertIn("does not endorse", text)

    def test_cost_main_exit_codes(self):
        import cost
        self.copy_csv()
        rc, out, _ = run_main(cost, ["--offline", "--strict"])
        self.assertEqual(rc, 0)
        self.assertNotIn("INCOMPLETE", out)


class TestMetrics(Base):
    def _agg(self, drop_mystery=False):
        import cost, metrics, common
        self.copy_csv()
        if drop_mystery:
            p = self.data / "daily_by_model.csv"
            p.write_text("".join(l for l in p.read_text().splitlines(True) if "mystery-model" not in l))
        with redirect_stderr(io.StringIO()):
            prices, _ = cost.load_prices(offline=True)
        enriched = metrics.enrich_rows(metrics.read_model_rows(), prices)
        task_agg, _ = common.read_tasks()
        return metrics, metrics.aggregate_by_day_agent(enriched, task_agg)

    def test_hermes_tokens_per_prompt_not_blank(self):
        metrics, agg = self._agg()
        h = metrics.metric_values(agg[("2026-11-10", "hermes")], None)
        self.assertEqual(h["prompts"], 4)                          # (unknown) prompts counted (M1)
        self.assertAlmostEqual(h["nonCacheTokensPerPrompt"], 14250.0)
        c = metrics.metric_values(agg[("2026-11-10", "claude")], None)
        self.assertAlmostEqual(c["nonCacheTokensPerPrompt"], 22000.0)   # M2: no cache read in numerator
        self.assertAlmostEqual(c["totalTokensPerPrompt"], 222000.0)
        self.assertAlmostEqual(c["cacheHitRatio"], 1_000_000 / 1_100_000)  # MINOR 9: output excluded

    def test_cost_per_task_restricted_to_agents_with_tasks(self):
        metrics, agg = self._agg()
        keys = [k for k in agg if k[0] == "2026-11-10"]
        val, note, agents, excluded = metrics.pooled_cost_per_task(agg, keys)
        self.assertIsNone(val)
        self.assertEqual((note, agents), (metrics.NA_ALL_FAILED, ["codex"]))
        self.assertEqual(excluded, [(("2026-11-10", "hermes"), metrics.NA_UNPRICED)])
        self.assertEqual(metrics.agent_cost_per_task(agg[("2026-11-10", "codex")]), (None, metrics.NA_ALL_FAILED))
        self.assertEqual(metrics.agent_cost_per_task(agg[("2026-11-10", "claude")]), (None, metrics.NA_NO_TASKS))
        self.assertEqual(metrics.agent_cost_per_task(agg[("2026-11-12", "hermes")]), (None, metrics.NA_NO_USAGE))
        metrics, agg = self._agg(drop_mystery=True)
        keys = [k for k in agg if k[0] == "2026-11-10"]
        val, note, agents, excluded = metrics.pooled_cost_per_task(agg, keys)
        self.assertAlmostEqual(val, 0.084)     # (hermes $0 + codex $0.21) / 2.5 — claude's $0.47 NOT included
        self.assertEqual(agents, ["codex", "hermes"])
        self.assertEqual(metrics.agent_cost_per_task(agg[("2026-11-10", "hermes")]), (0.0, "free: no paid usage"))
        period = metrics.pooled_cost_per_task(agg, list(agg))
        self.assertAlmostEqual(period[0], 0.084)          # Σ/Σ; 2026-11-12 hermes excluded (no usage)
        self.assertEqual(period[3], [(("2026-11-12", "hermes"), metrics.NA_NO_USAGE)])

    def test_calendar_trends_and_single_date_mode(self):
        metrics, agg = self._agg()
        t = metrics.compute_trends(agg)
        self.assertEqual(t[("2026-11-12", "claude")]["deltaVsPrev"], 55000)   # vs 2026-11-11 (=0), not vs 11-10
        self.assertIsNone(t[("2026-11-12", "claude")]["avg7d"])
        self.assertIsNone(t[("2026-11-10", "claude")]["deltaVsPrev"])
        self.assertNotIn(("2026-11-12", "hermes"), t)                       # task-only entry: no trend
        synth = {("2026-11-01", "x"): dict(metrics._new_agg(), hasUsage=True, tokens=70),
                 ("2026-11-07", "x"): dict(metrics._new_agg(), hasUsage=True, tokens=0)}
        self.assertAlmostEqual(metrics.compute_trends(synth)[("2026-11-07", "x")]["avg7d"], 10.0)
        self.copy_csv()
        rc, out, _ = run_main(metrics, ["2026-11-12", "--offline"])
        self.assertEqual(rc, 0)
        self.assertIn("+55,000", out)

    def test_metrics_report_sections_and_csv(self):
        import csv, metrics
        self.copy_csv()
        rc, out, _ = run_main(metrics, ["--offline", "--report"])
        self.assertEqual(rc, 0)
        md = (self.data / "metrics_report.md").read_text()
        for s in ("Token/biaya ≠ produktivitas", "### Tidak terhitung", "### Model free", "Snapshot terbaru",
                  "fetched_at", "cacheRead / (input + cacheRead + cacheWrite)", "n/a (all tasks failed, weight 0)",
                  "Cost per task (periode)"):
            self.assertIn(s, md)
        with open(self.data / "metrics_daily.csv") as f:
            rows = list(csv.DictReader(f))
        h = [r for r in rows if r["agent"] == "hermes" and r["date"] == "2026-11-10"][0]
        self.assertEqual((h["nonCacheTokensPerPrompt"], h["costStatus"], h["costPerTask"], h["costPerTaskNote"]),
                         ("14250.00", "partial", "", "n/a (unpriced tokens)"))
        with open(self.data / "metrics_by_agent.csv") as f:
            by_model = list(csv.DictReader(f))
        g = [r for r in by_model if r["model"] == "GLM-5.3-flash-free"][0]
        self.assertEqual((g["kind"], g["costUSD"]), ("free", "0.00"))


class TestWeeklyAndReports(Base):
    def test_week_window_length(self):
        import weekly, common
        self.copy_snapshots()
        snaps = common.load_all_snapshots()
        start, end, days = weekly.week_window(snaps, None)       # last snapshot 2026-11-11 (Wed)
        self.assertEqual((str(start), str(end), len(days)), ("2026-11-09", "2026-11-11", 3))
        start, end, days = weekly.week_window(snaps, date(2026, 11, 3))
        self.assertEqual((days[0], days[-1], len(days)), ("2026-11-03", "2026-11-09", 7))
        with self.assertRaises(ValueError):
            weekly.week_window(snaps, date(2026, 11, 12))
        rc, _, err = run_main(weekly, ["--week-start", "2026-11-12"])
        self.assertEqual(rc, 2)
        rc, _, _ = run_main(weekly, [])                       # default window 2026-11-09..11
        self.assertEqual(rc, 0)
        import csv
        with open(self.data / "weekly.csv") as fh:
            w = list(csv.DictReader(fh))
        self.assertEqual([r["sessions"] for r in w if r["agent"] == "hermes" and r["date"] == "2026-11-10"], ["2"])
        self.assertIn("(3 hari, belum lengkap)", (self.data / "report_week.md").read_text())
        rc, _, _ = run_main(weekly, ["--week-start", "2026-11-02"])
        self.assertEqual(rc, 0)
        md = (self.data / "report_week.md").read_text()
        self.assertIn("Minggu 2026-11-02 s/d 2026-11-08 (7 hari)", md)
        self.assertIn("Cache write", md)
        self.assertIn("Snapshot terbaru", md)

    def test_collect_report_columns(self):
        import collect, common
        self.copy_snapshots()
        with redirect_stdout(io.StringIO()):
            collect.build_report(common.load_all_snapshots(), days=7)
        md = (self.data / "report.md").read_text()
        self.assertIn("Non-cache (in+out)", md)
        self.assertIn("**Total semua agent**", md)
        self.assertIn("| hermes | model-rows | 35 | 25 | 10 | 0 | 0 | 35 | 4 |", md)
        self.assertIn("pecahan 0–1", md)
        self.assertIn("Snapshot terbaru", md)


class TestCollect(Base):
    def _fake_bin(self):
        fake = self.tmp / "omarchy"
        (fake / "bin").mkdir(parents=True)
        for name, body in (("hermes", "echo '{\"name\":\"x\"}'\nexit 1"),
                           ("newagent", "exit 3"),
                           ("update", "touch \"$0.RAN\"\necho '{}'")):
            p = fake / "bin" / f"omarchy-agent-usage-{name}"
            p.write_text("#!/bin/sh\n" + body + "\n")
            p.chmod(0o755)
        return fake

    def test_never_runs_update_and_discovers_agents(self):
        import collect
        fake = self._fake_bin()
        with mock.patch.dict(os.environ, {"OMARCHY_PATH": str(fake)}), redirect_stdout(io.StringIO()):
            agents = collect.discover_agents()
            self.assertEqual(agents, ["hermes", "newagent"])
            with self.assertRaises(ValueError):
                collect.wrapper_path("update")
            self.assertEqual(collect.usage_record("hermes"), {"name": "x"})   # rc!=0 but JSON -> kept, logged
            self.assertIsNone(collect.usage_record("newagent"))               # rc!=0, no JSON -> None
            self.assertEqual(set(collect.usage_records(agents)), {"hermes"})
        self.assertFalse((fake / "bin" / "omarchy-agent-usage-update.RAN").exists())

    def test_parity_check(self):
        import collect
        rows = [{"day": "2026-11-10", "input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0},
                {"day": "2026-11-11", "input": 1, "output": 0, "cacheRead": 0, "cacheWrite": 0}]
        rec = {"recentDays": [{"date": "2026-11-10", "messageCount": 15}, {"date": "2026-11-11", "messageCount": 9}]}
        p = collect.parity_check(rows, rec, today="2026-11-11")
        self.assertTrue(p["ok"])                                   # only today's day differs
        self.assertEqual([m["day"] for m in p["mismatches"]], ["2026-11-11"])
        p = collect.parity_check(rows, rec, today="2026-11-12")
        self.assertFalse(p["ok"])
        self.assertFalse(collect.parity_check(rows, {}, "2026-11-12")["checked"])

    def test_all_chain_report_mode_offline(self):
        import collect
        self.copy_snapshots()
        rc, out, err = run_main(collect, ["--report", "--all", "--offline"])
        self.assertEqual(rc, 0)
        for n in ("daily.csv", "daily_by_model.csv", "report.md", "cost_report.md",
                  "metrics_report.md", "report_week.md", "weekly.csv"):
            self.assertTrue((self.data / n).exists(), n)
        self.assertFalse((self.tmp / "cache" / "pricing.json").exists())   # offline: no cache write


if __name__ == "__main__":
    unittest.main()
