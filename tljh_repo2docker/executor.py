from concurrent.futures import ThreadPoolExecutor

from tornado.ioloop import IOLoop


class Executor:
    """
    Mixin to execute functions in an executor
    """

    _executor = None

    def _run_in_executor(self, func, *args):
        cls = self.__class__
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(2)
        return IOLoop.current().run_in_executor(cls._executor, func, *args)
