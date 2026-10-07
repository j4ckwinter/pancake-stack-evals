from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from behavioral.review import CASES, consolidate, prepare_review, score, summarize


class ReviewEvaluationTests(unittest.TestCase):
    def test_cases_have_passing_local_tests_and_distinct_contract_outcomes(self):
        probes = {
            "keyword": "from billing import invoice_for_order; assert invoice_for_order(19.5) == {'amount': 19.5}",
            "consumer": "from producer import create_invoice; from consumer import read_total; assert read_total(create_invoice(19.5)) == 19.5",
            "archive": "import json; from pathlib import Path; from archive import read_total; assert read_total(json.loads(Path('archive.json').read_text())[0]) == 19.5",
        }
        with tempfile.TemporaryDirectory() as directory:
            for case in CASES:
                workspace = Path(directory) / case
                before = prepare_review(case, workspace)
                self.assertIn('billing.py', before)
                result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover'],
                                        cwd=workspace, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                for defect, probe in probes.items():
                    with self.subTest(case=case, probe=defect):
                        result = subprocess.run([sys.executable, '-B', '-c', probe],
                                                cwd=workspace, capture_output=True, text=True, timeout=10)
                        self.assertEqual(result.returncode == 0, case != defect, result.stderr)
                diff = (workspace / 'change.diff').read_text()
                self.assertIn('--- a/producer.py', diff)
                self.assertNotIn('billing.py', diff)

    def test_consolidation_preserves_surrounding_instructions(self):
        from target import source_root
        source = (source_root() / 'skills/check/SKILL.md').read_text()
        candidate = consolidate(source)
        self.assertLess(len(candidate), len(source))
        self.assertEqual(source.split('Read repository instructions')[0],
                         candidate.split('Read repository instructions')[0])
        self.assertEqual(source[source.index('Inspect changed comments'):],
                         candidate[candidate.index('Inspect changed comments'):])

    def test_summary_keeps_failed_runs_and_missing_usage_explicit(self):
        result = dict(run_id="run-01", case="keyword", variant="baseline", exit_code=0, timed_out=False,
                      sessions=[{"completed": True}], artifact={"passed": True},
                      preferences_unchanged=True, usage_complete=True,
                      usage_all_sessions={"total_tokens": 100}, elapsed_seconds=2,
                      tool_calls_all_sessions=3, command_actions_all_sessions=1)
        assessment = dict(run_id="run-01", case="keyword", detected=["keyword-api"], false_findings=0,
                          process={"contract_reads": True})
        failed = dict(result, run_id="run-02", exit_code=1, timed_out=True, usage_complete=False,
                      elapsed_seconds=0.1)
        summary = summarize([result, failed], [assessment, dict(assessment, run_id="run-02", detected=[])])["baseline"]
        self.assertEqual(summary["execution_failures"], 1)
        self.assertEqual(summary["miss_rate"], 0.5)
        self.assertEqual(summary["missing_usage_runs"], 1)
        self.assertEqual(summary["cost"]["elapsed_seconds"], {"n": 1, "median": 2, "min": 2, "max": 2})
        self.assertEqual(summary["process"]["contract_reads"]["passed"], 2)
        with self.assertRaises(ValueError):
            summarize([result], [])

    def test_summary_rejects_swapped_same_case_adjudications(self):
        with self.assertRaisesRegex(ValueError, "run identity"):
            summarize([{"run_id": "run-01", "case": "clean"}],
                      [{"run_id": "run-02", "case": "clean"}])

    def test_score_counts_misses_false_findings_and_deduplicates(self):
        self.assertEqual(score('keyword', [], 2), {
            'expected_defects': 1, 'detected_defects': 0, 'missed_defects': 1,
            'false_findings': 2, 'clean_control': False})
        self.assertEqual(score('keyword', ['keyword-api', 'keyword-api'], 0)['detected_defects'], 1)
        self.assertEqual(score('clean', [], 1)['false_findings'], 1)
        self.assertTrue(score('clean', [], 0)['clean_control'])
        with self.assertRaises(ValueError):
            score('clean', ['keyword-api'], 0)
        with self.assertRaises(ValueError):
            score('clean', [], -1)


if __name__ == '__main__':
    unittest.main()
