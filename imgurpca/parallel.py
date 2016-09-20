import threading
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty


class Parallel:

    def __init__(self, pkgs, common=None, nthreads=1):
        """
        @param pkgs (iterable): a list of objects passed one at a time to parallel_process
        @param common (anything): common arguments passed to every process (optional)
        @param nthreads (int): number of threads to run (preferably < len(pkgs))
        """
        self.nthreads = nthreads
        self.threads = []
        self.queue = Queue()
        self.results = Queue()
        self.common = common
        for pkg in pkgs:
            self.queue.put(pkg)

    def parallel_process(self, pkg, common):
        """override this function with whatever needs to be parallelized
        """
        pass

    def worker(self):
        while True:
            try:
                pkg = self.queue.get_nowait()
            except Empty:
                break
            self.results.put(self.parallel_process(pkg, self.common))
            self.queue.task_done()
        return

    def start(self):
        for i in range(self.nthreads):
            t = threading.Thread(target=self.worker)
            t.daemon = False
            t.start()
            self.threads.append(t)

    def wait_for_threads(self):
        for t in self.threads:
            t.join()

    def get_results(self):
        results = []
        while True:
            try:
                r = self.results.get_nowait()
            except Empty:
                break
            results.append(r)
        return results
