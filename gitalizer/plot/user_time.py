"""The main module for plotting user related graphs."""

import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from sqlalchemy import or_
from flask import current_app

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.plot.helper import get_user_repositories, plot_figure


def plot_user_punchcard(login, session, time_window=timedelta(days=3)):
    """Get all commits of repositories of an user."""
    delta = datetime.now() - timedelta(days=900)
    commits = db.session.query(Commit) \
        .filter(Commit.time >= delta) \
        .join(Email, or_(Email.email == Commit.author_email_address, Email.email == Commit.committer_email_address)) \
        .join(Contributer, Email.contributer_login == Contributer.login) \
        .filter(Contributer.login == login) \
        .all()

    plot_dir = current_app.config['PLOT_DIR']
    if not os.path.exists(plot_dir):
        os.mkdir(plot_dir)

    title = f"{login}'s Punchcard"

    plot_punchcard_from_commits(commits, title, plot_dir)


def plot_punchcard_from_commits(commits, title, path):
    """Plot a punchard from commits."""
    # Find how many plots we are making
    statistic = {}
    for commit in commits:
        weekday = commit.time.weekday()
        hour = commit.time.hour
        if weekday not in statistic:
            statistic[weekday] = {}
            for i in range(24):
                statistic[weekday][i] = 0
        statistic[weekday][hour] += 1

    punchcard = pd.DataFrame(statistic).transpose().stack().reset_index()
    punchcard.columns = ['day', 'hour', 'count']
    print(punchcard)

    # Create figure with axes
    fig = plt.figure(figsize=(8, title and 3 or 2.5), facecolor='#ffffff')
    ax = fig.add_subplot('111', axisbg='#ffffff')
    fig.subplots_adjust(left=0.06, bottom=0.04, right=0.98, top=0.95)

    # Set title
    ax.set_title(title, y=0.96).set_color('#333333')
    ax.set_frame_on(False)

    ax.scatter(punchcard['hour'], punchcard['day'], s=punchcard['count'], c='#333333', edgecolor='#444444')
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
    plt.show(block=True)

    import sys
    sys.exit(0)
