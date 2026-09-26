# -*- coding: utf-8 -*-
from collective.webhook.actions.webhook import EXECUTOR


def drain_executor():
    """Block until every webhook call submitted so far has finished.

    The executor has a single worker, so a no-op submitted now completes
    only after all the earlier calls.
    """
    EXECUTOR.submit(lambda: None).result(timeout=10)
