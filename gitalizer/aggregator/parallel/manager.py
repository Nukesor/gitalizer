"""Module for multiprocessing management."""
import multiprocessing
from flask import current_app

from gitalizer.aggregator.parallel.task import Task
from gitalizer.aggregator.parallel.worker import Worker


class Manager():
    """Class for managing various multiprocessing tasks."""

    def __init__(self, task_type: str, tasks: list,
                 sub_manager: 'Manager'=None):
        """Create a new manager."""
        self.tasks = set(tasks)
        self.task_type = task_type
        self.sub_manager = sub_manager

        self.task_queue = multiprocessing.JoinableQueue()
        self.result_queue = multiprocessing.Queue()
        self.consumer_count = current_app.config['GIT_SCAN_THREADS']

    def start(self):
        """Initialize workers and add initial tasks."""
        # Create and start normal consumer
        consumers = [Worker(self.task_queue, self.result_queue)
                     for i in range(self.consumer_count)]
        for w in consumers:
            w.start()

        for task in self.tasks:
            self.task_queue.put(Task(self.task_type, task))

    def add_tasks(self, tasks: list):
        """Add some tasks to the queue."""
        # Add unique tasks to queue
        tasks = set(tasks)
        for task in (tasks - self.tasks):
            print(f'Added task {task} for type {self.task_type}')
            self.task_queue.put(Task(self.task_type, task))

        # Add new tasks to task set.
        self.tasks += tasks

    def run(self):
        """All tasks are added. Process worker responses and wait for worker to finish."""
        # Start the sub manager
        if self.sub_manager is not None:
            print('Start sub manager.')
            self.sub_manager.start()

        # Poison pill for user scanner
        print('Add poison pills.')
        for _ in range(self.consumer_count):
            self.task_queue.put(None)

        finished_tasks = 0
        while finished_tasks < len(self.tasks):
            result = self.result_queue.get()

            if self.sub_manager is not None:
                self.sub_manager.add_tasks(result['tasks'])
            print(result['message'])
            if 'error' in result:
                print('Encountered an error:')
                print(result['error'])

        # All sub tasks have been added.
        # Wait for them to finish.
        self.sub_manager.run()
