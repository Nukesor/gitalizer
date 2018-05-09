"""Plot a punchcard from a bunch of commits."""
import pandas as pd
import matplotlib.pyplot as plt


class CommitPunchcard():
    """Punchcard creator."""

    def __init__(self, commits, path, title):
        """Create a new instance."""
        self.path = path
        self.title = title
        self.commits = commits
        self.data = None

    def run(self):
        """Execute all steps."""
        self.preprocess()
        self.plot()

    def preprocess(self):
        """Preprocess data into plottable form."""
        # Find how many plots we are making
        statistic = {}
        for weekday in range(7):
            statistic[weekday] = {}
            for i in range(24):
                statistic[weekday][i] = 0

        for commit in self.commits:
            weekday = commit.local_time().weekday()
            hour = commit.local_time().hour
            statistic[weekday][hour] += 1

        punchcard = pd.DataFrame(statistic).transpose().stack().reset_index()
        punchcard.columns = ['day', 'hour', 'count']
        self.raw_data = punchcard.copy()
        punchcard['count'] = punchcard['count'] * 5 / punchcard['count'].mean()
        self.data = punchcard

    def plot(self):
        """Plot the data."""
        # Create figure with axes
        background = '#ffffff'
        graph_color = '#333333'
        border_color = '#555555'

        fig = plt.figure(figsize=(20, 10), facecolor=background)

        # Set tick size
        plt.rc('xtick', labelsize=20)
        plt.rc('ytick', labelsize=20)

        fig.subplots_adjust(left=0.06, bottom=0.04, right=0.98, top=0.95)
        ax = fig.add_subplot(1, 1, 1)

        # Set title
        ax.set_title(self.title, y=1.10, fontsize=25).set_color(graph_color)
        ax.set_frame_on(False)

        ax.scatter(
            self.data['hour'],
            self.data['day'],
            s=self.data['count']*10,
            c=graph_color,
            edgecolor=border_color,
        )

        dist = -0.8
        ax.plot([dist, 23.5], [dist, dist], c='#555555')
        ax.plot([dist, dist], [dist, 6.4], c='#555555')

        # Set axis limit so we only see the wanted number range
        ax.set_xlim(-1, 24)
        ax.set_ylim(-0.9, 6.9)

        # Format y ticks
        ax.set_yticks(range(7))
        for tx in ax.set_yticklabels(['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']):
            tx.set_color('#555555')

        # Format x ticks
        ax.set_xticks(range(24))
        for tx in ax.set_xticklabels(['%02d' % x for x in range(24)]):
            tx.set_color('#555555')

        ax.set_aspect('equal')

        fig.savefig(self.path, bbox_inches='tight')
        plt.close(fig)
