"""Offline playbook checks: python -B -m unittest tests.test_playbooks."""
from datetime import date
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from bb import playbooks


class PlaybookTests(unittest.TestCase):
    def test_candidate_edit_and_registry_review(self):
        book = self.book()
        self.store.save(book)
        edited = dict(book, title='Reviewed route')
        self.assertEqual(self.store.edit(book['id'], edited)['title'], 'Reviewed route')
        self.assertEqual(self.store.snapshot()['playbooks'][0]['title'], 'Reviewed route')
        self.store.transition(book['id'], 'approve')
        with self.assertRaises(ValueError):
            self.store.edit(book['id'], edited)
        entry = dict(id='TD-1', provider='atlas', env='dev', description='Route',
                     params={'origin': 'LAX'}, date_rule='D+30', verified_at='2026-11-03',
                     verified_run='run-1', status='stale')
        self.store.add_testdata(entry)
        self.assertEqual(self.store.mark_status('atlas', 'dev', 'TD-1', 'ok')['status'], 'ok')
        self.assertEqual(self.store.snapshot()['testdata'][0]['status'], 'ok')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = playbooks.Store(self.root)

    def book(self, number=1, **changes):
        return dict(id=f'PB-search-{number:03}', status='candidate', family='search',
                    title='Search inventory', summary='Search preparation', tags=['search'],
                    providers=['atlas'], endpoints=['/v1/search'], endpoint_flow=['GET /v1/search'],
                    case_patterns=[{'pattern': 'GET /v1/search', 'needs': ['origin', 'destination']}],
                    testdata_refs=[], pitfalls=[], source_tasks=['SS-1'], last_verified='2026-11-03',
                    times_used=0, times_helped=0) | changes

    def test_search_ranks_confidence_freshness_and_provider(self):
        for book in (self.book(), self.book(2, times_used=10, times_helped=9),
                     self.book(3, times_used=10, times_helped=9, last_verified='2020-01-01'),
                     self.book(4, providers=['other'])):
            self.store.save(book)
            self.store.transition(book['id'], 'approve')
        self.store.save(self.book(5))
        found = self.store.search(['search', 'atlas', '/v1/search'], 'inventory', today=date(2026, 11, 3))
        self.assertEqual([b['id'] for b in found], ['PB-search-002', 'PB-search-001', 'PB-search-004'])
        self.assertEqual(self.store.search(['unrelated'], '', today=date(2026, 11, 3)), [])

    def test_relative_dates_and_stale_filter(self):
        entry = dict(id='TD-1', provider='atlas', env='dev', description='Route',
                     params={'origin': 'LAX', 'date': 'D+30', 'return_date': 'D+40'},
                     date_rule='D+30', verified_at='2026-11-03', verified_run='run-1', status='ok')
        self.store.add_testdata(entry)
        data = self.store.testdata('atlas', 'dev', today=date(2026, 11, 3))[0]
        self.assertEqual(data['date'], '2026-12-03')
        self.assertEqual(data['params']['return_date'], '2026-12-13')
        self.store.mark_stale('atlas', 'dev', 'TD-1')
        self.assertEqual(self.store.testdata('atlas', 'dev'), [])
        with self.assertRaises(ValueError):
            self.store.add_testdata(entry | {'date_rule': '2027-01-01'})

    def test_rejects_secrets_and_expectations_recursively(self):
        for changes in ({'pitfalls': ['Bearer ' + 'fake-credential']},
                        {'expected': 20}, {'case_patterns': [{'pattern': 'search', 'needs': [], 'tolerance': 1}]},
                        {'summary': 'Expected price is 20'}, {'summary': 'Permission to retry'},
                        {'summary': 'Extra edge cases: malformed dates'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.store.save(self.book(**changes))
        self.assertFalse((self.root / 'playbooks/PB-search-001.json').exists())

    def test_transitions_and_idempotent_usage(self):
        self.store.save(self.book())
        self.store.transition('PB-search-001', 'approve')
        self.store.record_use('PB-search-001', True, 'run-1')
        self.store.record_use('PB-search-001', True, 'run-1')
        self.assertEqual(self.store.stats()['used'], 1)
        self.assertEqual(self.store.stats()['helped'], 1)
        self.store.transition('PB-search-001', 'deprecate')
        self.assertEqual(self.store.search(['search']), [])
        with self.assertRaises(ValueError):
            self.store.record_use('PB-search-001', True, 'run-2')
        self.store.save(self.book(2))
        self.assertEqual(self.store.transition('PB-search-002', 'reject')['status'], 'deprecated')

    def make_run(self):
        run = self.root / 'run'
        run.mkdir()
        (run / 'ticket-scope.md').write_text('# SS-1\nSearch only; no retry.\n')
        plan = dict(v=1, task='SS-1', environment='dev', family='search', providers=['atlas'],
                    cases=[dict(case_id='TC-1', title='Must return expected 42',
                                steps=['GET /v1/search'], expected={'price': 42},
                                test_data={'provider': 'atlas', 'params': {'origin': 'LAX', 'date': '2026-12-03'}})])
        (run / 'cases.json').write_text(json.dumps(plan))
        result = dict(case_id='TC-1', status='need_action', duration_ms=1,
                      actual={'reason_code': 'NO_DATA', 'request_executed': True}, action_needed='Supply inventory')
        (run / 'results.jsonl').write_text(json.dumps(result) + '\n')
        return run

    def test_distill_requires_approval_and_is_idempotent(self):
        run = self.make_run()
        with self.assertRaises(ValueError):
            self.store.distill(run, 'SS-1')
        book = self.store.distill(run, 'SS-1', approved=True, today=date(2026, 11, 3))
        self.assertEqual(book['status'], 'candidate')
        self.assertEqual(book['endpoint_flow'], ['GET /v1/search'])
        self.assertNotIn('42', json.dumps(book))
        self.assertEqual(book['pitfalls'], ['NO_DATA: usable inventory was unavailable'])
        self.assertEqual(self.store.testdata('atlas', 'dev'), [])
        self.assertEqual(self.store.distill(run, 'SS-1', approved=True)['id'], book['id'])
        self.assertEqual(self.store.stats()['need_action'], {'NO_DATA': 1})
        self.store.transition(book['id'], 'approve')
        entry = self.store.testdata('atlas', 'dev', today=date(2026, 11, 3))[0]
        self.assertEqual(entry['date_rule'], 'D+30')
        self.assertEqual(entry['params']['date'], '2026-12-03')

    def test_malformed_and_incomplete_runs_fail_without_writes(self):
        run = self.make_run()
        (run / 'results.jsonl').write_text('{broken\n')
        with self.assertRaises(ValueError):
            self.store.distill(run, 'SS-1', approved=True)
        self.assertFalse((self.root / 'playbooks').exists())
        (self.root / 'playbooks').mkdir()
        (self.root / 'playbooks/PB-search-001.json').write_text('{}')
        with self.assertRaises(ValueError):
            self.store.search(['search'])

    def test_classifier_reason_is_preserved_without_learning_response(self):
        run = self.make_run()
        result = dict(case_id='TC-1', status='failed', duration_ms=1, actual='Mismatch',
                      failure={'assertion': 'Price must equal 42',
                               'response': {'status': 200, 'body_excerpt': '{"message":"unknown"}'}})
        (run / 'results.jsonl').write_text(json.dumps(result) + '\n')
        book = self.store.distill(run, 'SS-1', approved=True)
        self.assertEqual(book['pitfalls'], ['CONTRACT_MISMATCH: a ticket assertion failed'])
        self.assertNotIn('42', json.dumps(book))

    def test_reason_codes_with_expected_substring_are_allowed(self):
        self.store.save(self.book(pitfalls=['UNEXPECTED_MESSAGE: provider message was unrecognized']))

    def test_rejected_data_does_not_create_store(self):
        entry = dict(id='TD-1', provider='atlas', env='dev', description='Route',
                     params={'nested': {'expected_price': 2}}, date_rule='D+30',
                     verified_at='2026-11-03', verified_run='run-1', status='candidate')
        with self.assertRaises(ValueError):
            self.store.add_testdata(entry)
        self.assertFalse(self.store.books.exists())

    def test_unexecuted_need_action_does_not_register_planned_data(self):
        run = self.make_run()
        result = dict(case_id='TC-1', status='need_action', duration_ms=0,
                      actual={'reason_code': 'AUTH_MISSING'}, action_needed='Supply runtime access')
        (run / 'results.jsonl').write_text(json.dumps(result) + '\n')
        book = self.store.distill(run, 'SS-1', approved=True)
        self.assertEqual(book['testdata_refs'], [])
        self.assertEqual(self.store.stats()['need_action'], {'AUTH_MISSING': 1})

    def test_oversized_search_is_bounded_and_malformed_log_rejected(self):
        self.store.save(self.book(pitfalls=['inventory ' * 4000]))
        self.store.transition('PB-search-001', 'approve')
        self.assertLessEqual(len(json.dumps(self.store.search(['search'])).encode()), 12000)
        self.store.log.write_text('{bad\n')
        with self.assertRaises(ValueError):
            self.store.transition('PB-search-001', 'deprecate')

    def test_cli_search_is_compact_json(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'bb.playbooks', '--root', str(self.root),
                                 'search', '--tags', 'search', '--top', '3'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

    def test_distill_recovers_after_snapshot_write_failure(self):
        run = self.make_run()
        write = playbooks.write_json
        def interrupted(path, value):
            if path.parent == self.store.books:
                raise OSError('simulated interruption')
            write(path, value)
        with patch('bb.playbooks.write_json', side_effect=interrupted), self.assertRaises(OSError):
            self.store.distill(run, 'SS-1', approved=True, today=date(2026, 11, 3))
        self.store.distill(run, 'SS-1', approved=True, today=date(2026, 11, 3))
        self.assertEqual(self.store.stats()['need_action'], {'NO_DATA': 1})


if __name__ == '__main__':
    unittest.main()
