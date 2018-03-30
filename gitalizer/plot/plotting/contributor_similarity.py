"""Plot a punchcard from a bunch of commits."""
import matplotlib.pyplot as plt
from pprint import pprint

from gitalizer.plot.plotting import CommitPunchcard
from gitalizer.helpers.db import get_user_commits_from_repositories


class CommitSimilarity():
    """Commit simliarity of several contributors."""

    def __init__(self, user, repositories, delta, path, title):
        """Create new missing time plotter."""
        self.user = user
        self.repositories = repositories
        self.delta = delta

        self.path = path
        self.title = title
        self.fig = plt.figure()

        self.data = {}

    def run(self):
        """Execute all steps."""
        self.preprocess()
        self.plot()

    def preprocess(self):
        """Prepare all data for plotting."""
        punchcard_data = {}
        for _, user in enumerate(self.user):
            commits = get_user_commits_from_repositories(
                user,
                self.repositories,
                self.delta,
            )
            plotter = CommitPunchcard(commits, '', '')
            plotter.preprocess()
            punchcard_data[user.login] = plotter.raw_data

        # Normalize data for better comparison
        for _, df in punchcard_data.items():
            mean = df['count'].mean()
            df['count'] = df['count']/mean

        for name, df in punchcard_data.items():
            self.data[name] = {}

            # Compare every other contributer with the current contributer.
            for comparison_name, comparison_df in punchcard_data.items():
                if name == comparison_name:
                    continue

                # Get euclidean distance of both series
                euclidean_distance = comparison_df['count'] - df['count']
                euclidean_distance = euclidean_distance.abs()
                euclidean_distance = euclidean_distance.sum()

                # Get matching percentage
                length = df['count'].size
                percentage = 100*((2*length-euclidean_distance)/(2*length))

                self.data[name][comparison_name] = percentage

        pprint(self.data)

    def get_ax(self):
        """Create a new axes object on the main figure."""
        ax = self.fig.add_subplot(1, 1, 1)
        return ax

    def plot(self):
        """Plot the data."""
        ax = self.get_ax()

        ax.set_aspect('equal')

        self.fig.savefig(self.path)
        plt.close(self.fig)
