# -*- coding: utf-8 -*-
from collective.webhook.actions.datamanager import DataManager

import transaction
import unittest


class DataManagerTests(unittest.TestCase):
    def setUp(self):
        transaction.abort()

    def tearDown(self):
        transaction.abort()

    def test_callable_runs_only_after_commit(self):
        calls = []
        transaction.get().join(DataManager(calls.append, ("x",)))
        self.assertEqual([], calls)
        transaction.commit()
        self.assertEqual(["x"], calls)

    def test_callable_does_not_run_on_abort(self):
        calls = []
        aborted = []
        transaction.get().join(
            DataManager(calls.append, ("x",), onAbort=lambda: aborted.append(True))
        )
        transaction.abort()
        self.assertEqual([], calls)
        self.assertEqual([True], aborted)

    def test_abort_without_callback(self):
        calls = []
        transaction.get().join(DataManager(calls.append, ("x",)))
        transaction.abort()
        self.assertEqual([], calls)

    def test_callable_does_not_run_when_another_manager_fails_the_commit(self):
        calls = []

        class Failing(DataManager):
            def tpc_vote(self, txn):
                raise RuntimeError("vote failed")

        transaction.get().join(DataManager(calls.append, ("x",)))
        transaction.get().join(Failing(lambda: None))
        with self.assertRaises(RuntimeError):
            transaction.commit()
        transaction.abort()
        self.assertEqual([], calls)

    def test_vote_is_called_with_args(self):
        votes = []
        transaction.get().join(DataManager(lambda *a: None, ("x",), vote=votes.append))
        transaction.commit()
        self.assertEqual(["x"], votes)

    def test_failing_callable_is_logged_and_does_not_break_commit(self):
        def fail():
            raise RuntimeError("boom")

        transaction.get().join(DataManager(fail))
        with self.assertLogs("collective.webhook", "ERROR") as logs:
            transaction.commit()
        self.assertIn("Failed in tpc_finish", logs.records[0].getMessage())

    def test_no_subtransaction_support(self):
        dm = DataManager(lambda: None)
        self.assertIsNone(dm.abort_sub(None))
        self.assertIsNone(dm.commit_sub(None))
        self.assertIsNone(dm.beforeCompletion(None))
        self.assertIsNone(dm.afterCompletion(None))
        self.assertIsNone(dm.commit(None))
        with self.assertRaises(AssertionError):
            dm.tpc_begin(None, subtransaction=True)

    def test_sort_key_sorts_last(self):
        self.assertTrue(DataManager(lambda: None).sortKey().startswith("~"))

    def test_savepoint(self):
        dm = DataManager(lambda: None)
        self.assertIsNotNone(dm.savepoint())
