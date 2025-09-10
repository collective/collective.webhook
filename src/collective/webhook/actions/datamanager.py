from transaction.interfaces import IDataManager
from zope.interface import implementer

import logging
import transaction


logger = logging.getLogger("collective.webhook")


@implementer(IDataManager)
class DataManager(object):
    def __init__(self, callable, args=(), vote=None, onAbort=None):
        self.callable = callable
        self.args = args
        self.vote = vote
        self.onAbort = onAbort
        # Use the default thread transaction manager.
        self.transaction_manager = transaction.manager

    def commit(self, txn):
        pass

    def abort(self, txn):
        if self.onAbort:
            self.onAbort()

    def sortKey(self):
        return "~" + str(id(self))

    # No subtransaction support.
    def abort_sub(self, txn):
        """This object does not do anything with subtransactions"""
        pass

    commit_sub = abort_sub

    def beforeCompletion(self, txn):
        """This object does not do anything in beforeCompletion"""
        pass

    afterCompletion = beforeCompletion

    def tpc_begin(self, txn, subtransaction=False):
        assert not subtransaction

    def tpc_vote(self, txn):
        if self.vote is not None:
            return self.vote(*self.args)

    def tpc_finish(self, txn):
        try:
            self.callable(*self.args)
        except Exception:
            # Any exceptions here can cause database corruption.
            logger.exception("Failed in tpc_finish for %r", self.callable)

    tpc_abort = abort

    def savepoint(self):
        return transaction._transaction.NoRollbackSavepoint(self)
