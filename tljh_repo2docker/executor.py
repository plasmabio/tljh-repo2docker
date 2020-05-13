from concurrent.futures import ThreadPoolExecutor

from tornado.ioloop import IOLoop

class DockerExecutor:
    """
    Mixin to run docker commands in an executor
    """

    _docker_executor = None

    def _run_in_executor(self, func, *args):
        cls = self.__class__
        if cls._docker_executor is None:
            cls._docker_executor = ThreadPoolExecutor(2)
        return IOLoop.current().run_in_executor(cls._docker_executor, func, *args)
