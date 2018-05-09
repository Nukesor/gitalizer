"""Plot a punchcard from a bunch of commits."""
import math
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

        self.data = {}

    def run(self):
        """Execute all steps."""
        self.preprocess()

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

        self.normalize(punchcard_data)

        for name, df in punchcard_data.items():
            self.data[name] = {}

            # Compare every other contributer with the current contributer.
            for comparison_name, comparison_df in punchcard_data.items():
                if name == comparison_name:
                    continue

                self.data[name][comparison_name] = self.euclidean_distance(df, comparison_df)

        pprint(self.data)

    def normalize(self, data):
        """Normalize data for better comparison."""
        for _, df in data.items():
            mean = df['count'].mean()
            df['count'] = df['count']/mean

    def euclidean_distance(self, origin_data, compare_data):
        """Compute the euclidean distance of two punchcards."""
        difference = compare_data['count'] - origin_data['count']
        difference = difference.pow(2)
        return math.sqrt(difference.sum())

    def get_ax(self):
        """Create a new axes object on the main figure."""
        ax = self.fig.add_subplot(1, 1, 1)
        return ax

    def plot(self):
        """Plot the data."""
        self.fig = plt.figure()
        ax = self.get_ax()

        ax.set_aspect('equal')

        self.fig.savefig(self.path)
        plt.close(self.fig)
