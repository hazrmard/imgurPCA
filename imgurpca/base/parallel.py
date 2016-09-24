import threading
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

# The Parallel class provides a framework for running multiple tasks in separate
# threads. Usefule for network IO operations or automated side-tasks.

class Parallel:

    def __init__(self, pkgs, common=None, nthreads=1):
        """
        @param pkgs (iterable): a list of objects passed one at a time to parallel_process
        @param common (anything): common arguments passed to every process (optional)
        @param nthreads (int): number of threads to run (preferably < len(pkgs))
        """
        self.nthreads = nthreads        # total number of spawned threads
        self.threads = []               # list of thread objects
        self.queue = Queue()            # queue containing args for individual thread
        self.results = Queue()          # queue containing return vals of parallel_process
        self.common = common            # common arguments for all threads
        self.lock = threading.Lock()    # in case there is resource sharing
        self.callback = None            # callback function
        self.cargs = []                 # arguments for callback func
        self.ckwargs = {}               # keyword args for callback func
        self.cthread = None             # callback thread
        for pkg in pkgs:
            self.queue.put(pkg)


    def parallel_process(self, pkg, common):
        """override this function with whatever needs to be parallelized
        """
        pass


    def worker(self):
        """wrapper for parallel_process. Keeps calling until the pkg queue is
        empty.
        """
        while True:
            try:
                pkg = self.queue.get_nowait()
            except Empty:
                break
            self.results.put(self.parallel_process(pkg, self.common))
            self.queue.task_done()
        return


    def start(self):
        """adds threads to self.threads and starts them.
        """
        self.threads = []
        for i in range(self.nthreads):
            t = threading.Thread(target=self.worker)
            t.daemon = False
            t.start()
            self.threads.append(t)
        if self.cthread is not None:
            self.cthread.start()


    def wait_for_threads(self):
        for t in self.threads:
            t.join()


    def still_running(self):
        """checks if threads are still runnning.
        Returns a boolean.
        """
        if len(self.threads):
            status = all([t.isAlive() for t in self.threads])
        else:
            status = False
        return status


    def set_callback(self, func, args=(), kwargs={}):
        """sets up a function to call after spawned threads have finished. The
        callback wrapper runs in a separate daemon thread and continuously queries
        running threads. Once all threads have finished running, it calls the
        self.callback function.
        @param func (func): a callable function object
        @param args (list/tuple): positional arguments
        @param kwargs (dict): keyword arguments
        """
        self.callback = func
        self.cargs = args
        self.ckwargs = kwargs
        def callback_wrapper(parallel_instance):
            parallel_instance.wait_for_threads()
            parallel_instance.callback(*parallel_instance.cargs, **parallel_instance.ckwargs)
        self.cthread = threading.Thread(target=callback_wrapper, args=(self,))
        self.cthread.daemon = True


    def get_results(self):
        """converts results in the queue to a list. Quits as soon as the queue is
        empty. So should be called after wait_for_threads() to ensure all threads
        have finished.
        """
        results = []
        while True:
            try:
                r = self.results.get_nowait()
            except Empty:
                break
            results.append(r)
        return results
