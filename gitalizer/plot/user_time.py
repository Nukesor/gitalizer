"""The main module for plotting user related graphs."""

import os
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedFormatter
from datetime import timedelta

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.plot.helper import get_user_repositories, plot_figure


def plot_user_punchcard(name, session, time_window=timedelta(days=3)):
    """Get all commits of repositories of an user."""
    contributer = db.session.query(Contributer) \
        .filter(Contributer.login.ilike(name)) \
        .one_or_none()

    if contributer is None:
        print(f'No contributer with name {name}')
        return

    path = os.path.join(path, 'repo_changes')
    if not os.path.exists(path):
        os.mkdir(path)

    repositories = get_user_repositories(contributer)

    plot_all_user_commits(contributer, repositories, path)

    for repository in repositories:
        plot_user_repository_changes(contributer, repository, path)


def plot_punchcard_from_commits(df, metric='lines', title='punchcard', by=None):
    """Plot a punchard.

    :param df:
    :param metric:
    :param title:
    :return:
    """
    # Find how many plots we are making
    if by is not None:
        unique_vals = set(df[by].values.tolist())
    else:
        unique_vals = ['foo']
    for idx, val in enumerate(unique_vals):
        if by is not None:
            sub_df = df[df[by] == val]
        else:
            sub_df = df
        # Create figure with axes
        fig = plt.figure(figsize=(8, title and 3 or 2.5), facecolor='#ffffff')
        ax = fig.add_subplot('111', axisbg='#ffffff')
        fig.subplots_adjust(left=0.06, bottom=0.04, right=0.98, top=0.95)

        # Set title
        if by is not None:
            ax.set_title(f'{title}: {val}', y=0.96).set_color('#333333')
        else:
            ax.set_title(title, y=0.96).set_color('#333333')
        ax.set_frame_on(False)

        ax.scatter(sub_df['hour_of_day'], sub_df['day_of_week'], s=sub_df[metric], c='#333333', edgecolor='#333333')
        for line in ax.get_xticklines() + ax.get_yticklines():
            line.set_alpha(0.0)

        dist = -0.8
        ax.plot([dist, 23.5], [dist, dist], c='#555555')
        ax.plot([dist, dist], [dist, 6.4], c='#555555')
        ax.set_xlim(-1, 24)
        ax.set_ylim(-0.9, 6.9)
        ax.set_yticks(range(7))
        for tx in ax.set_yticklabels(['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']):
            tx.set_color('#555555')
            tx.set_size('x-small')
        ax.set_xticks(range(24))
        for tx in ax.set_xticklabels(['%02d' % x for x in range(24)]):
            tx.set_color('#555555')
            tx.set_size('x-small')
        ax.set_aspect('equal')
        if idx + 1 == len(unique_vals):
            plt.show(block=True)
        else:
            plt.show(block=False)
