import logging

from engage.utils.class_overrides import MonkeyPatcher

from wsgiref.handlers import BaseHandler

from traceback import TracebackException

import json

class BaseHandlerOverrides(MonkeyPatcher):
    """
    Override the base handler for WSGI so we can log exceptions using the standard python logger
    """
    patch_class = BaseHandler

    def log_exception(self,exc_info):
        """
        Log out as json
        :param exc_info:
        :return:
        """
        try:
            stderr = self.get_stderr()
            self.print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                self.traceback_limit, stderr
            )
            stderr.flush()
        finally:
            exc_info = None

    def print_exception(self, etype, value, tb, limit=None, file=None, chain=True):
        exc_output = ""

        for line in TracebackException(
                type(value), value, tb, limit=limit).format(chain=chain):
            exc_output += line

        exc_output = exc_output.replace("\n","\\n")

        logging.error(str(value), extra = {
            "ex": value.__class__.__name__,
            "traceback": exc_output,
        })