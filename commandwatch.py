import re
import sys
from subprocess import PIPE, Popen
from threading import Thread
from queue import Queue, Empty
import os
import time
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError


class CommandWatch():
    """
    CommandWatch runs given command and checks number of times given regex is encountered from the output of command.
    It records and returns time taken beginning from first line of output or first time start pattern is encountered.
    It can optionally be set to run for specified length of time.
    """
    q = Queue()
    p = None
    readThread = None
    countdown = 0
    end_pattern = None
    start_timer_pattern = None
    match_pattern = None
    env = None
    cmd = None
    matched_lines = []

    class Enqueue(Thread):
        out = None
        queue = None

        def __init__(self, out, queue):
            super().__init__()
            self.out = out
            self.daemon = True
            self.queue = queue

        def run(self) -> None:
            try:
                for line in iter(self.out.readline, b''):
                    self.queue.put(line)
            except:
                pass
            self.out.stdout.close()

    def __init__(self, cmd, countdown, end_pattern, match_pattern=None, start_timer_pattern=None, env=None):
        """
        @param cmd: Command to run
        @param countdown: Check end_pattern is matched as many times from cmd output
        @param end_pattern: pattern to match for countdown
        @param start_timer_pattern: Optional start of timer
        """
        self.cmd = cmd
        self.countdown = countdown
        self.end_pattern = re.compile(end_pattern)
        if start_timer_pattern:
            self.start_timer_pattern = re.compile(start_timer_pattern)
        if match_pattern:
            self.match_pattern = re.compile(match_pattern)
        self.env = env

    def submit(self, timer=0):
        self.p = Popen([self.cmd], stdout=PIPE, bufsize=1, env=self.env,
                       universal_newlines=True, shell=True, executable='/bin/bash', preexec_fn=os.setsid)
        self.readThread = CommandWatch.Enqueue(self.p.stdout, self.q)
        executor = ThreadPoolExecutor(1)
        future = executor.submit(self.run, timer)
        return future

    def run(self, timer=0):
        """
        Run command and record running time
        @param timer: Run for given number of seconds, Optional (defaults to 0, meaning run forever or till pattern is matched count number of times)
        @return:
        """
        if not self.p:
            self.p = Popen([self.cmd], stdout=PIPE, bufsize=1,
                           universal_newlines=True, shell=True, executable='/bin/bash', preexec_fn=os.setsid)
        if not self.readThread:
            self.readThread = CommandWatch.Enqueue(self.p.stdout, self.q)

        self.readThread.start()
        count = 0
        t_end = time.time() + timer
        start_time = time.time()
        started = False
        while (timer == 0 or time.time() < t_end) and count < self.countdown:
            try:
                line = self.q.get_nowait()
            except Empty:
                pass
            else:  # got line
                if not started:
                    if self.start_timer_pattern and self.start_timer_pattern.match(line):
                        start_time = time.time()
                        started = True
                        continue
                    else:
                        start_time = time.time()
                        started = True
                if self.end_pattern and self.end_pattern.match(line):
                    count += 1
                if self.match_pattern and self.match_pattern.match(line):
                    self.matched_lines.append(line)
        end_time = time.time()
        time.sleep(1)
        os.killpg(os.getpgid(self.p.pid), signal.SIGTERM)
        time.sleep(1)
        self.readThread.join()
        print('Completed : ' + self.cmd)
        return end_time - start_time


if __name__ == "__main__":
    randomEchoWatch = CommandWatch(
        cmd="export BROWSER='/bin/echo';aws sso login",
        countdown=1,
        end_pattern="Successully logged into Start URL: https://d-92670b2743.awsapps.com/start",
        match_pattern="https://device\.sso\.us-west-2\.amazonaws\.com/\?user_code=[a-zA-Z0-9-]+")
    future = randomEchoWatch.submit(30)
    print("Some task...")
    try:
        print("Time taken: " + str(future.result()) + " s")
        print(f'{randomEchoWatch.matched_lines}')
    except TimeoutError as err:
        print("Time out!")
