"""Plot a punchcard from a bunch of commits."""
import pandas as pd
import matplotlib.pyplot as plt


def plot_commit_punchcard(commits, path, title):
    """Plot a punchard from commits."""
    # Find how many plots we are making
    statistic = {}
    for commit in commits:
        weekday = commit.commit_time.weekday()
        hour = commit.commit_time.hour
        if weekday not in statistic:
            statistic[weekday] = {}
            for i in range(24):
                statistic[weekday][i] = 0
        statistic[weekday][hour] += 1

    punchcard = pd.DataFrame(statistic).transpose().stack().reset_index()
    punchcard.columns = ['day', 'hour', 'count']
    punchcard['count'] = punchcard['count'] * 5 / punchcard['count'].mean()

    # Create figure with axes
    background = '#ffffff'
    graph_color = '#333333'
    border_color = '#555555'

    fig = plt.figure(figsize=(20, 10), facecolor=background)
    fig.subplots_adjust(left=0.06, bottom=0.04, right=0.98, top=0.95)
    ax = fig.add_subplot(1, 1, 1)

    # Set title
    ax.set_title(title, y=0.96).set_color(graph_color)
    ax.set_frame_on(False)

    ax.scatter(
        punchcard['hour'],
        punchcard['day'],
        s=punchcard['count']*10,
        c=graph_color,
        edgecolor=border_color,
    )

    dist = -0.8
    ax.plot([dist, 23.5], [dist, dist], c='#555555')
    ax.plot([dist, dist], [dist, 6.4], c='#555555')

    ax.set_xlim(-1, 24)
    ax.set_ylim(-0.9, 6.9)

    # Format y ticks
    ax.set_yticks(range(7))
    for tx in ax.set_yticklabels(['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']):
        tx.set_color('#555555')
        tx.set_size('x-small')

    # Format x ticks
    ax.set_xticks(range(24))
    for tx in ax.set_xticklabels(['%02d' % x for x in range(24)]):
        tx.set_color('#555555')
        tx.set_size('x-small')

    ax.set_aspect('equal')

    fig.savefig(path)
    plt.close(fig)
