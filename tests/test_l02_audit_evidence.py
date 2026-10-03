"""Read-only evidence tests for the L02 prompt audit; no chat/model requests."""
import json
import unittest
from pathlib import Path
import l02_eval as runner

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/l02-clean-lesson-02-20261003-202039.json'

class L02AuditEvidenceTests(unittest.TestCase):
    def test_capture_lesson02_prompt_and_existing_red_case_trace(self):
        data = json.loads(REPORT.read_text(encoding='utf-8-sig'))
        record = next(r for r in data['records'] if r['id'] == 'C-01'
                      and r['profile'] == 'lesson-02' and r['run'] == 3)
        health = runner.stand('GET', '/health')
        self.assertEqual(health['profile'], 'lesson-02', 'Requires existing lesson-02; does not change profiles')
        prompt = runner.stand('GET', '/api/_test/prompt')
        tree = runner.stand('GET', '/api/_test/traces/' + record['request_id'])
        self.assertEqual(tree['request_id'], record['request_id'])
        self.assertEqual(tree['attributes']['run.profile'], 'lesson-02')
        self.assertIn('D05', tree['attributes']['run.active_defects'])
        self.assertIn('D05', prompt['overlays'])
        self.assertTrue(prompt['text'])
        names = [s['name'] for s in runner.spans(tree)]
        self.assertFalse(any(n.startswith('tool.') for n in names))
        self.assertEqual(sum(n == 'llm.call' for n in names), record['agent']['llm_calls'])
        out = ROOT / 'evidence/l02-audit'
        out.mkdir(parents=True, exist_ok=True)
        for name, value in [('health.json', health), ('assembled-prompt.json', prompt),
                            ('C-01-run3.trace.json', tree)]:
            (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Captured existing evidence; request_id=' + record['request_id'])
        print('No chat calls, resets, clock/profile changes or model requests')
