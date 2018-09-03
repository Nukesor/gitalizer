"""Queue processing workers."""
import time
import multiprocessing

from gitalizer.extensions import sentry


class Worker(multiprocessing.Process):
    """A worker which gets tasks from a queue."""

    def __init__(self, task_queue, result_queue):
        """Create a new worker."""
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        """Process incoming tasks."""
        while True:
            try:
                next_task = self.task_queue.get()
                # Poison pill received: Shutdown
                if next_task is None:
                    self.task_queue.task_done()
                    break
                answer = next_task()
                self.task_queue.task_done()
                self.result_queue.put(answer)
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except BaseException:
                sentry.captureException()
        return
