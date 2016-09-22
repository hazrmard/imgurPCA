from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from imgurpca.base import Parallel
import threading
import time

# The Electronic class is a base class for all automated tasks (see Bot).
# It can be subclassed with additional authentication functions to act on
# behalf of a user.

class Electronic(object):

    MINUTE = 60
    HOUR = 3600
    DAY = 86400
    WEEK = 604800

    def __init__(self, *args, **kwargs):
        self._interval = None   # interval in s for auto tasks
        self._func = None       # task to perform after _interval
        self._args = []         # list of args to be passed to _func
        self._taskthread = None # thread spawned on Bot().go()
        self._until = -1        # time limit on running task

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


    def go(self):
        """begin scheduled task. Derives and runs Parallel instance with 1 thread.
        """
        class Task(Parallel):
            def parallel_process(self, pkg, common):
                function = common[0]
                stop_flag = common[1]
                interval = common[2]
                until = common[3]
                while not (stop_flag.is_set() or (until>0 and time.time()>=until)):
                    function(*pkg)
                    time.sleep(interval)

        self._task = Task([self._args], nthreads=1)
        self._task.common = [self._func, threading.Event(), self._interval, self._until]
        self._task.start()


    def stop(self):
        """stop the task after it comes out of sleep for next execution"""
        self._task.common[1].set()
