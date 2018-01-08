"""Plot the timeline of additions and deletions."""
import os
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from gitalizer.plot.helper.plot import plot_figure


def plot_commit_timeline(commits, path, title):
    """Plot the changes of commits."""
    data = []
    for c in commits:
        if not c.additions or not c.deletions:
            continue
        if (math.fabs(c.additions) + math.fabs(c.deletions)) > 8000:
            continue
        data.append({
            'date': c.time.replace(tzinfo=None),
            'additions': c.additions,
            'deletions': -c.deletions,
        })

    # Basic dataframe by date (month)
    df = pd.DataFrame(data=data)
    df = df.sort_values(by='date')
    df.set_index('date', drop=True, inplace=True)

    # Format dataframe for plotting
    df = df.stack().reset_index()
    df.columns = ['date', 'vars', 'vals']
    df['timestamp'] = df[['date']].apply(lambda x: x[0].timestamp(), axis=1)
    df.set_index('date', drop=True, inplace=True)

    # Create and specify figure
    fig, ax = plt.subplots()
    fig.set_figheight(20)
    fig.set_figwidth(40)
    fig.suptitle(title, fontsize=30)

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
    grouped = df.groupby('vars')
    for key, group in grouped:
        # Remove the low 1st and 99th percentile
        group = group[group.vals < group.vals.quantile(.99)]
        group = group[group.vals > group.vals.quantile(.01)]
        group = group.reset_index()

        plt.sca(ax)
        plt.scatter(group.date.dt.to_pydatetime(), group.vals, color=colors[key], label=key)

    # Create legend
    ax.legend()
    plot_figure(path, ax)

    return
