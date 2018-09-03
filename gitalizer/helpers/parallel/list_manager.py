"""A multiprocess manager for handling tasks."""
import multiprocessing

from gitalizer.extensions import logger
from gitalizer.helpers import get_config
from gitalizer.helpers.parallel.task import Task
from gitalizer.helpers.parallel.worker import Worker


class ListManager():
    """Class for managing various multiprocessing tasks."""

    def __init__(self, task_type: str, tasks: list,
                 sub_manager: 'Manager'=None):
        """Create a new manager."""
        self.tasks = tasks
        self.task_type = task_type
        self.sub_manager = sub_manager
        self.started = False

        self.task_queue = multiprocessing.JoinableQueue()
        self.result_queue = multiprocessing.Queue()
        self.results = []
        self.consumer_count = get_config().GIT_COMMIT_SCAN_THREADS

    def start(self):
        """Initialize workers and add initial tasks."""
        # Create and start normal consumer
        consumers = [Worker(self.task_queue, self.result_queue)
                     for i in range(self.consumer_count)]
        for w in consumers:
            w.start()

        for task in self.tasks:
            self.task_queue.put(Task(self.task_type, task))
        self.started = True

    def add_tasks(self, tasks: list):
        """Add some tasks to the queue."""
        # Add unique tasks to queue
        if self.started:
            for task in tasks:
                self.task_queue.put(Task(self.task_type, task))

        self.tasks += tasks

    def run(self):
        """All tasks are added. Process worker responses and wait for worker to finish."""
        # Start the sub manager
        if self.sub_manager is not None:
            logger.info('Start sub manager.')

        # Poison pill for user scanner
        logger.info('Add poison pills.')
        for _ in range(self.consumer_count+1):
            self.task_queue.put(None)

        logger.info(f'Processing {len(self.tasks)} tasks')
        finished_tasks = 0
        while finished_tasks < len(self.tasks):
            logger.info(f'Waiting: {finished_tasks} of {len(self.tasks)}')
            result = self.result_queue.get()
            self.results.append(result)

            logger.info(result['message'])
            if 'error' in result:
                logger.info('Encountered an error:')
                logger.info(result['error'])
            elif self.sub_manager is not None:
                self.sub_manager.add_tasks(result['tasks'])
            finished_tasks += 1

        # All sub tasks have been added.
        # Wait for them to finish.
        if self.sub_manager is not None:
            self.sub_manager.start()
            self.sub_manager.run()
