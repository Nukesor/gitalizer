"""Plot the timeline of additions and deletions."""
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

from gitalizer.plot.helper.plot import plot_figure

week_days = ['Mon', 'Tue', 'Wen', 'Thu', 'Fri', 'Sat', 'Sun']


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


class MissingTime():
    """Compute a timeline with missing time."""

    def __init__(self, raw_data, path, title):
        """Create new missing time plotter."""
        self.path = path
        self.title = title
        self.raw_data = raw_data
        self.data = None

        self.entries = []
        self.anomalies = []
        self.current_entry = {}

    def run(self):
        """Execute all steps."""
        self.preprocess()
        self.plot()

    def preprocess(self):
        """Preprocess the data for plotting."""
        timeline = CommitTimeline(self.raw_data, self.path, self.title)
        timeline.preprocess()

        # Sort commits by week and mark each day with a commit as a working day
        by_week = {n: g for n, g in timeline.data.groupby(pd.Grouper(freq='W'))}
        week_vectors = []
        for week, commits in by_week.items():
            days = [0] * 7
            for time, _ in commits.iterrows():
                days[time.weekday()] = 1

            vector = [week.year, week.isocalendar()[1]] + [sum(days)] + days
            week_vectors.append(vector)

        # Create a dataframe for sorting and easier processing
        data = pd.DataFrame(
            week_vectors,
            columns=['year', 'week', 'working_days'] + week_days,
        )

        # Create a fingerprint row for easier prototype detection.
        def fingerprint(row):
            return row.ix[2:10].astype('U').str.cat(sep=',')
        data['fingerprint'] = data.apply(fingerprint, axis=1)

        entry = None
        prototype = None
        for index, row in data.iterrows():
            # We currently have no prototype. Try to find one.
            if prototype is None:
                prototype = self.find_prototype(data.loc[index:index+6])
                prototype, entry = self.create_new_entry(prototype, row, entry)
                self.check_anomaly(prototype, row)

                continue

            # Identical fingerprint (same week workday pattern)
            if row.fingerprint == prototype.fingerprint:
                continue

            prototype_exists = self.check_for_prototype(prototype, data.loc[index:index+6])
            # We couldn't find the prototype in the next few rows
            # Mark the previous entry as finished and start a new one.
            if not prototype_exists:
                entry['end'] = [row.year, row.week]
                self.entries.append(entry)
                entry = None

                # Try to find a new prototype.
                prototype = self.find_prototype(data.loc[index:index+6])
                prototype, entry = self.create_new_entry(prototype, row, entry)

            # Check if the current row is a anomaly
            self.check_anomaly(prototype, row)

        entry['end'] = [date.today().year, date.today().isocalendar()[1]]
        self.entries.append(entry)

        print(self.entries)
        print(self.anomalies)
        print(data)
        self.data = data

    def find_prototype(self, data, last_prototype=None):
        """Look at the first few days and get the current prototype."""
        # Create an entry for each fingerprint and count the occurrences of this entry
        counter = {}
        for _, row in data.iterrows():
            fingerprint = row.fingerprint
            if fingerprint not in counter:
                counter[fingerprint] = {
                    'prototype': row,
                    'count': 1,
                }
            else:
                counter[fingerprint]['count'] += 1

        # Get the prototype for the fingerprint with the most occurrences
        #
        # If there is no row which solely has the most occurences, return None.
        # In this case we can't predict a proper prototype.
        max_count = 0
        invalid = False
        prototype = None
        for _, item in counter.items():
            if item['count'] > max_count:
                prototype = item['prototype']
                max_count = item['count']
                invalid = False
            elif item['count'] == max_count:
                invalid = True

        if invalid:
            return None

        return prototype

    def check_for_prototype(self, prototype, data):
        """Check if there is an instance of the current prototype in the next few rows."""
        for _, row in data.iterrows():
            if row['fingerprint'] == prototype['fingerprint']:
                return True

        return False

    def check_similarity(self, prototype, row):
        """Check if a row is close to the current prototype."""
        working_days_diff = math.fabs(row['working_days'] - prototype['working_days'])
        different_days = 0
        for day in week_days:
            if row[day] != prototype[day]:
                different_days += 1

        # Shifted a day to another day.
        if working_days_diff == 0:
            if different_days <= 1:
                return True

        # A single day missing
        if working_days_diff == 1:
            if different_days <= 1:
                return True

        return False

    def create_new_entry(self, prototype, row, last_entry):
        """Create a new entry."""
        # We found a prototype. Save it and mark it.
        # Check if the current row is the prototype. Otherwise we handle it as unknown.
        empty_week = row.working_days == 0
        if prototype is not None and (prototype == row).all() and not empty_week:
            # If there is a entry from a previous unknown time span,
            # add an end date for this time span and add it.
            if self.current_entry:
                last_entry['end'] = [row.year, row.week]
                self.entries.append(last_entry)

            new_entry = {
                'type': 'normal',
                'prototype': prototype,
                'start': [row.year, row.week],
            }

        else:
            # If no prototype has been found, the type 'unknown' will be used.
            new_entry = {
                'type': 'unknown',
                'start': [row.year, row.week],
            }
            prototype = None

        return prototype, new_entry

    def check_anomaly(self, prototype, row):
        """Check if this entry is an anomaly."""
        if row['working_days'] <= 1:
            self.anomalies.append([row.year, row.week])

        if prototype is not None:
            similar = self.check_similarity(prototype, row)
            if not similar:
                self.anomalies.append([row.year, row.week])

        return
