"""Plot the timeline of additions and deletions."""
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from gitalizer.plot.helper.plot import plot_figure


class CommitTimeline():
    """Timeline creator."""

    def __init__(self, raw_data, path, title):
        """Create a new instance."""
        self.path = path
        self.title = title
        self.raw_data = raw_data
        self.data = None

    def run(self):
        """Execute all steps."""
        self.preprocess()
        self.plot()

    def preprocess(self):
        """Preprocess data for plotting."""
        data = []
        for commit in self.raw_data:
            if not commit.additions or not commit.deletions:
                continue
            if (math.fabs(commit.additions) + math.fabs(commit.deletions)) > 8000:
                continue
            data.append({
                'date': commit.local_time(),
                'additions': commit.additions,
                'deletions': -commit.deletions,
            })

        # Basic dataframe by date (month)
        data = pd.DataFrame(data=data)
        data = data.sort_values(by='date')
        data.set_index('date', drop=True, inplace=True)

        # Format dataframe for plotting
        data = data.stack().reset_index()
        data.columns = ['date', 'vars', 'vals']
        data['timestamp'] = data[['date']].apply(lambda x: x[0].timestamp(), axis=1)
        data.set_index('date', drop=True, inplace=True)

        self.data = data

    def plot(self):
        """Plot the changes of commits."""
        # Create and specify figure
        fig, ax = plt.subplots()
        fig.set_figheight(20)
        fig.set_figwidth(40)
        fig.suptitle(self.title, fontsize=30)

        # We only want to see years as xaxis labels .
        years = mdates.YearLocator()
        yearsFmt = mdates.DateFormatter('%Y')
        ax.xaxis.set_major_locator(years)
        ax.xaxis.set_major_formatter(yearsFmt)

        colors = {
            'additions': 'green',
            'deletions': 'crimson',
        }

        # Create scatter plot for additions and deletions
        grouped = self.data.groupby('vars')
        for key, group in grouped:
            # Remove the low 1st and 99th percentile
            group = group[group.vals < group.vals.quantile(.99)]
            group = group[group.vals > group.vals.quantile(.01)]
            group = group.reset_index()

            plt.sca(ax)
            plt.scatter(group.date.dt.to_pydatetime(), group.vals, color=colors[key], label=key)

        # Create legend
        ax.legend()
        plot_figure(self.path, ax)

        return
