"""The main module for plotting user related graphs."""

import os
import math
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FixedFormatter
from sqlalchemy import or_

from gitalizer.extensions import db
from gitalizer.models.email import Email
from gitalizer.models.commit import Commit
from gitalizer.models.contributer import Contributer
from gitalizer.plot.helper import get_user_repositories, plot_figure


def plot_user_repositories_changes(name, path):
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


def plot_user_repository_changes(contributer, repo, path):
    """Plot the changes for a specific contributer and repository."""
    commits = db.session.query(Commit) \
        .filter(Commit.repository == repo) \
        .join(Email, or_(Email.email == Commit.author_email_address, Email.email == Commit.committer_email_address)) \
        .join(Contributer, Email.contributer_login == Contributer.login) \
        .filter(Contributer.login == contributer.login) \
        .all()

    if len(commits) < 20:
        return

    data = []
    for c in commits:
        if not c.additions or not c.deletions:
            continue
        if (math.fabs(c.additions) + math.fabs(c.deletions)) > 8000:
            continue
        time = c.time.replace(
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

    plt.title(f'Commit size history for repository `{repo.name}` and contributer `{contributer.login}`')
    plot_path = os.path.join(path, repo.name)
    plot_figure(plot_path, box)

    return


def plot_all_user_commits(contributer, repositories, path):
    """Plot the changes of all repositories for a specific contributer."""
    urls = [r.clone_url for r in repositories]
    commits = db.session.query(Commit) \
        .filter(Commit.repository_url.in_(urls)) \
        .join(Email, Email.email == Commit.author_email_address) \
        .join(Contributer, Email.contributer_login == Contributer.login) \
        .filter(Contributer.login == contributer.login) \
        .all()

    # Gather commits
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
    fig.suptitle(f"{contributer.login}'s commit size history.", fontsize=30)

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

    plot_path = os.path.join(path, 'all_changes')
    plot_figure(plot_path, ax)

    return
