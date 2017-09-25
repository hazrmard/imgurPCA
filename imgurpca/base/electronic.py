from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from . import Parallel
import threading
import time

# The Electronic class is a base class for all automated tasks (see Bot).
# It can be subclassed with additional authentication functions to act on
# behalf of a user.

class Electronic(object):

    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800

    def __init__(self, *args, **kwargs):
        self._interval = 0      # interval in s for auto tasks
        self._func = None       # task to perform after _interval
        self._args = []         # list of args to be passed to _func
        self._task = None        # instance of derived Parallel running on _taskthread
        self._until = -1        # time limit on running task
        self._n = -1            # times to call automated task

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])


    def every(self, interval):
        """Specify interval for automated bot functions. Any arithmetic combination
        of Bot.MINUTE, Bot.HOUR, Bot.DAY, Bot.WEEK. Interval is the time between
        when the function finishes execution and starts again.
        """
        self._interval = interval
        return self


    def do(self, func):
        """specify a function that the bot does every interval. The function
        should not return anything. And results that might be needed elsewhere
        should assigned to one or more references passed as function arguments
        in using().
        @param func (function): a function object
        """
        self._func = func
        return self


    def using(self, args):
        """specify a list of arguments that the function in 'do' uses.
        @param args (list/tuple): a list of arguments to be passed to the funcion.
        """
        self._args = args
        return self


    def until(self, when):
        """specify a time when to stop running the task. By default runs forever.
        @param when (int): epoch time in seconds
        """
        self._until = when
        return self


    def times(self, n):
        """
        specify how many times to perform the task. The automated process ends
        when time limit in until() is reached, or function in do() is called
        'n' times, whichever comes first.
        @param n (int): number of times to perform task.
        """
        self._n = n
        return self


    def go(self):
        """begin scheduled task. Derives and runs Parallel instance with 1 thread.
        """
        class Task(Parallel):
            def parallel_process(self, pkg, common):
                function = common[0]
                stop_flag = common[1]
                interval = common[2]
                until = common[3]
                n = common[4]
                i=0
                while not (stop_flag.is_set() or (until>0 and time.time()>=until) or (n>0 and i>=n)):
                    function(*pkg)
                    i+=1
                    time.sleep(interval)
                stop_flag.clear()   # clear stop flag once loop ends

        self._task = Task([self._args], nthreads=1)
        self._task.common = [self._func, threading.Event(), self._interval, self._until, self._n]
        self._task.start()


    def stop(self, force=False):
        """stop the task after it comes out of sleep for next execution"""
        self._task.common[1].set()
        if force:
            self._task.threads[0].join(timeout=0)
        else:
            self._task.threads[0].join()

        self._until = -1    # reset all parameters
        self._n = -1
        self._args = []
        self._interval = 0
        self._func = None
        self._task = None
