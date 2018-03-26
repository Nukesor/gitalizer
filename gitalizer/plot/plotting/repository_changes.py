"""Plot the changes as a box plot for a user."""
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from matplotlib.ticker import FixedFormatter


def plot_repository_changes(commits, path, title):
    """Plot the changes for a specific contributor and repository."""
    data = []
    for c in commits:
        if not c.additions or not c.deletions:
            continue
        if (math.fabs(c.additions) + math.fabs(c.deletions)) > 8000:
            continue
        time = c.local_time().replace(
            day=1, hour=0, minute=0,
            second=0, microsecond=0,
            tzinfo=None,
        )
        data.append({
            'date': time,
            'additions': c.additions,
            'deletions': c.deletions,
            'changes': math.fabs(c.additions - c.deletions),
        })

    # Basic dataframe by date (month)
    df = pd.DataFrame(data=data)
    df = df.sort_values(by='date')
    df = df.set_index('date', drop=True)

    # Format dataframe for plotting
    df_stacked = df.stack()
    df_stacked = df_stacked.reset_index()
    df_stacked.columns = ['date', 'vars', 'vals']
    df_stacked.set_index('date', drop=True, inplace=True)

    # Create box plot
    box = sns.boxplot(x=df_stacked.index, y='vals', hue='vars', data=df_stacked)

    # Format dates
    dates = df_stacked.index.unique().to_series()
    dates = dates.dt.strftime('%Y-%m')
    box.xaxis.set_major_formatter(FixedFormatter(dates))

    plt.title(title)

    plt.xticks(rotation=30)
    plt.figure(figsize=(20, 10))
    box.savefig(path)

    plt.close(box)

    return
