"""A task for the multiprocessing worker."""


class Task(object):
    """An object which is passed to a worker."""

    def __init__(self, task_type, task):
        """Create a new object."""
        self.task = task
        self.task_type = task_type

    def __call__(self):
        """Actual work logic."""
        if self.task_type == 'github_contributor':
            from gitalizer.aggregator.github.user import get_user_repos
            return get_user_repos(self.task)
        elif self.task_type == 'github_repository':
            from gitalizer.aggregator.github.repository import get_github_repository
            return get_github_repository(self.task)
        elif self.task_type == 'analyse_travel_path':
            from gitalizer.analysis.travel_path import analyse_contributer_travel_path
            return analyse_contributer_travel_path(self.task)
        elif self.task_type == 'analyse_punchcard':
            from gitalizer.analysis.punchcard import get_punchcard_data
            return get_punchcard_data(self.task)
        elif self.task_type == 'github_user':
            from gitalizer.aggregator.github.user import get_user_data
            return get_user_data(self.task)
