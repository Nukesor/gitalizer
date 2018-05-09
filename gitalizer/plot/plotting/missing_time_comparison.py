"""Plot the timeline of additions and deletions."""
from datetime import datetime
from matplotlib import rcParams
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates

from gitalizer.helpers.db import get_user_commits_from_repositories
from gitalizer.plot.plotting import MissingTime

week_days = ['Mon', 'Tue', 'Wen', 'Thu', 'Fri', 'Sat', 'Sun']


class MissingTimeComparison():
    """Compute a timeline with missing time."""

    def __init__(self, user, repositories, delta, path, title):
        """Create new missing time plotter."""
        self.user = user
        self.repositories = repositories
        self.delta = delta

        self.scatter_draw = [
            [datetime.utcnow()-self.delta, datetime.utcnow()],
            [0, 0],
        ]

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

        weeks = mdates.WeekdayLocator(byweekday=mdates.MO)
        weeksFmt = mdates.DateFormatter('%Y-%W')
        ax.xaxis.set_major_locator(weeks)
        ax.xaxis.set_major_formatter(weeksFmt)

        return ax

    def plot(self):
        """Plot the figure."""
        rcParams['axes.titlepad'] = 20
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        for index, plotter in self.results.items():
            ax = self.add_ax(index)
            ax.set_ylim([-10, 10])
            ax = plotter.get_ax(parent_ax=ax)

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
            ax.legend(handles, labels, prop={'size': 20})
            ax.set_title(self.user[index].login, y=0.96, fontsize=30)
            ax.get_yaxis().set_ticks([])
            ax.scatter(self.scatter_draw[0], self.scatter_draw[1], color='white')
            plt.xticks(rotation=50)

        self.fig.subplots_adjust(hspace=1.0)
        self.fig.set_figheight(5*len(self.results))
        self.fig.set_figwidth(40)
        self.fig.suptitle(self.title, fontsize=30)

        self.fig.savefig(self.path, bbox_inches='tight')
        plt.close(self.fig)

        return
