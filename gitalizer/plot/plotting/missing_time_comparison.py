"""Plot the timeline of additions and deletions."""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

from gitalizer.plot.helper.db import get_user_commits_from_repositories
from gitalizer.plot.helper.plot import plot_figure
from gitalizer.plot.plotting import MissingTime

week_days = ['Mon', 'Tue', 'Wen', 'Thu', 'Fri', 'Sat', 'Sun']


class MissingTimeComparison():
    """Compute a timeline with missing time."""

    def __init__(self, user, repositories, delta, path, title):
        """Create new missing time plotter."""
        self.user = user
        self.repositories = repositories
        self.delta = delta

        self.path = path
        self.title = title
        self.fig = plt.figure()

        self.results = {}

    def run(self):
        """Execute all steps."""
        self.preprocess()
        self.plot()

    def preprocess(self):
        """Prepare all data for plotting."""
        for index, user in enumerate(self.user):
            commits = get_user_commits_from_repositories(
                user,
                self.repositories,
                self.delta,
            )
            plotter = MissingTime(commits, '', '')
            plotter.preprocess()
            self.results[index] = plotter

    def add_ax(self, index):
        """Create and specify figure."""
        ax = self.fig.add_subplot(len(self.results), 1, index+1)

        # We only want to see years as xaxis labels .
        years = mdates.YearLocator()
        yearsFmt = mdates.DateFormatter('%Y')
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)

        weeks = mdates.WeekdayLocator(byweekday=mdates.MO)
        weeksFmt = mdates.DateFormatter('%W')
        ax.xaxis.set_minor_locator(weeks)
        ax.xaxis.set_minor_formatter(weeksFmt)

        return ax

    def plot(self):
        """Plot the figure."""
        for index, _ in enumerate(self.results):
            ax = self.add_ax(index)
            ax.set_ylim([-10, 10])
            ax = self.results[index].get_ax(parent_ax=ax)

            handles, labels = ax.get_legend_handles_labels()
            handles = [
                patches.Patch(color='yellow', label='Work pattern unknown'),
                patches.Patch(color='blue', label='Work pattern exists'),
                patches.Patch(color='red', label='Work pattern anomaly'),
            ]
            labels = [
                'Work pattern unknown ',
                'Work pattern exists',
                'Work pattern anomaly',
            ]
            ax.legend(handles, labels)
            ax.set_title(self.user[index].login, fontsize=20)
            ax.get_yaxis().set_ticks([])
            ax.scatter()

        self.fig.set_figheight(20)
        self.fig.set_figwidth(40)
        self.fig.suptitle(self.title, fontsize=30)

        plt.xticks(rotation=30)
        self.fig.savefig(self.path)
        plt.close(self.fig)

        return
