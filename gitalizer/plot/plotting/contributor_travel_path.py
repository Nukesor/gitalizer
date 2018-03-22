"""Plot the changes as a box plot for a user."""
import os
import cartopy
import numpy as np
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import timedelta, datetime
from pycountry import countries as pycountries

from gitalizer.extensions import db
from gitalizer.models import Commit, TimezoneInterval
from gitalizer.timezone import timezone_country, map_timezone_to_utc


class TravelPath():
    """Travel path display."""

    def __init__(self, commits: Commit, path):
        """Create a new instance."""
        self.path = path
        self.raw_data = commits
        self.data = None
        if not os.path.exists(path):
            os.makedirs(path)

    def run(self):
        """Do everything."""
        self.preprocess()
        self.get_geo_data()
        self.plot()

    def preprocess(self):
        """Print the travel history of a contributor."""
        timezone_sets = []
        current_timezones = None
        last_valid = None
        change_at_day = None
        timezones_candidate = None

        for commit in self.raw_data:
            commit_time = commit.commit_time
            commit_timezone = commit.commit_time_offset
            if commit_timezone is None:
                continue

            zones = db.session.query(TimezoneInterval.timezone) \
                .filter(TimezoneInterval.start <= commit_time) \
                .filter(TimezoneInterval.end > commit_time) \
                .filter(TimezoneInterval.utcoffset == commit_timezone) \
                .all()

            # Create the initial timezone
            if current_timezones is None:
                current_timezones = {
                    'set': set([z[0] for z in zones]),
                    'start': commit_time.date(),
                    'end': commit_time.date(),
                }
                last_valid = commit_time.date()

                continue
            # We got a timezone and need to check if we are still in it or if there is a change
            else:
                # Get possible timezone candidates for this commit and intersect them with the current_timezones set
                timezone_set = set([z[0] for z in zones])
                intersection = timezone_set & current_timezones['set']
                # Check if the possible timezones of this commit matches any timezone of the current set.
                if len(intersection) > 0:
                    # By reassigning the intersected set we gain additional precision by considering possible specific DST changes
                    current_timezones['set'] = intersection
                    current_timezones['end'] = commit_time.date()
                    last_valid = commit_time.date()

                # There is no match between the possible timezones and the current set.
                # In this case we need to check if this is a single occurrence (anomaly) or
                # If this is an actual change.
                else:
                    # No change_at_day exists, but we detected a change
                    # Remember the change. If this change lasts for at least a day it will be marked.
                    if change_at_day is None:
                        change_at_day = commit.commit_time.date()
                        timezones_candidate = {
                            'set': set([z[0] for z in zones]),
                            'start': commit_time.date(),
                            'end': commit_time.date(),
                        }

            # No change detected
            if change_at_day is None:
                continue

            # There was an anomaly, but not for a whole day.
            # This could for instance be a developer committing from a remote server.
            if change_at_day <= last_valid:
                change_at_day = None
                timezones_candidate = None

                continue

            # The change is not older than a day
            # ignore it until the change lasts for longer than a day
            if change_at_day <= last_valid:
                continue

            # There exists a change from the last day.
            duration = current_timezones['end'] - current_timezones['start']

            # The current_timezones set exists only for a single day.
            # This is most likely an outlier. Thereby drop it and restore the last timezone.
            if duration < timedelta(days=1) and len(timezone_sets) > 0:
                last_timezone = timezone_sets.pop()
                last_timezone['end'] = current_timezones['end']
                current_timezones = last_timezone

                # Check if the old timezone_set and the current candidate actually match
                # If that's the case drop the candidate and completely replace the current_timezones set
                intersection = timezones_candidate['set'] & current_timezones['set']
                if len(intersection) > 0:
                    # Update current_timezone
                    current_timezones['set'] = intersection
                    current_timezones['end'] = commit_time.date()

                    # Reset candidate and last_valid occurrence
                    last_valid = commit_time.date()
                    change_at_day = None
                    timezones_candidate = None

                    continue

            # We detected a change and it seems to be valid.
            # Save the current timezone and set the candidate as the current timezone.
            timezone_sets.append(current_timezones)
            current_timezones = timezones_candidate
            change_at_day = None
            timezones_candidate = None
            last_valid = commit_time.date()

        current_timezones['end'] = datetime.now().date()
        timezone_sets.append(current_timezones)

        self.data = timezone_sets

    def get_geo_data(self):
        """Get Geo data from natural earth."""
        # Get all countries and create a dictionary by name
        countries_shp = shpreader.natural_earth(
            resolution='10m',
            category='cultural',
            name='admin_0_countries',
        )
        self.countries = list(shpreader.Reader(countries_shp).records())
        self.countries_by_name = {}
        self.countries_by_iso_a2 = {}
        for country in shpreader.Reader(countries_shp).records():
            self.countries_by_name[country.attributes['NAME_LONG']] = country
            self.countries_by_iso_a2[country.attributes['ISO_A2']] = country

        # Get all states and create a dictionary by name
        states_provinces_shp = shpreader.natural_earth(
            resolution='50m',
            category='cultural',
            name='admin_1_states_provinces',
        )
        self.states = list(shpreader.Reader(states_provinces_shp).records())
        self.states_by_name = {}
        for state in shpreader.Reader(states_provinces_shp).records():
            self.states_by_name[state.attributes['name']] = country

        # Get all timezones and create a dictionary by name
        timezones_shp = shpreader.natural_earth(
            resolution='10m',
            category='cultural',
            name='time_zones',
        )
        self.timezones = list(shpreader.Reader(timezones_shp).records())
        self.timezones_by_name = {}
        for timezone in shpreader.Reader(timezones_shp).records():
            # Try to get the actual name. Something like `Europe/Berlin`
            timezone_name = timezone.attributes['tz_name1st']
            # If there is no name, we default to the utc offset name `-5` `+4.5`
            if timezone_name == '':
                timezone_name = timezone.attributes['name']

            if timezone_name not in self.timezones_by_name.keys():
                self.timezones_by_name[timezone_name] = timezone

    def get_ax(self, data):
        """Create and populate new axes object."""
        timezone = list([x for x in data if 'UTC' in x])

        timezone_start = tuple((x/255 for x in (0, 255, 0, 100)))
        country_start = tuple((x/255 for x in (0, 150, 0)))
        # We ignore some countries, as they are too big and need a higher
        # resolution for precise timezone assignment.
        ignored_countries = ['United States', 'Australia', 'Brazil', 'Canada']

        ax = plt.axes(projection=ccrs.PlateCarree())

        # Print countries and state borders
        ax.add_feature(cartopy.feature.LAND)
        ax.add_feature(cartopy.feature.OCEAN)
        ax.add_feature(cartopy.feature.COASTLINE)
        ax.add_feature(cartopy.feature.BORDERS)
        for state in self.states:
            ax.add_geometries(
                state.geometry,
                ccrs.PlateCarree(),
                facecolor=np.array((240, 240, 220)) / 256,
                edgecolor='black',
                label=state.attributes['name'],
            )

        collected_countries = []
        collected_timezones = []
        for name in data:
            # Color the timezone if we find one
            name = map_timezone_to_utc(name)
            if name in self.timezones_by_name:
                timezone = self.timezones_by_name[name]

                # Prevent timezone from being applied multiple times.
                utc_name = timezone.attributes['utc_format']
                if utc_name not in collected_timezones:
                    collected_timezones.append(utc_name)

                    ax.add_geometries(
                        timezone.geometry,
                        ccrs.PlateCarree(),
                        facecolor=timezone_start,
                        label=name,
                    )

            # Check if we find a country for this timezone and draw it
            if name in timezone_country:
                # Check if we have a country code for this timezone
                country_code = timezone_country[name]

                # We have no country for this code.
                # Unfortunately the natural earth database is a little inconsistent.
                # Try to get the full name of the country by using pycountry
                # and resolve the country by this name.
                if country_code not in self.countries_by_iso_a2:
                    try:
                        name = pycountries.get(alpha_2=country_code).name
                    except KeyError:
                        continue

                    # We found a full name for this code.
                    # Check if we have a country for this name.
                    if name not in self.countries_by_name:
                        continue

                    # We found a country for this name. Proceed
                    country = self.countries_by_name[name]

                else:
                    country = self.countries_by_iso_a2[country_code]

                if country.attributes['NAME_LONG'] in ignored_countries:
                    continue

                # Avoid to draw the same country multiple times
                country_name = country.attributes['NAME_LONG']
                if country_name in collected_countries:
                    continue

                collected_countries.append(country_name)
                ax.add_geometries(
                    country.geometry,
                    ccrs.PlateCarree(),
                    facecolor=country_start,
                    edgecolor='black',
                    label=country_name,
                )


#        import sys
#        sys.exit()
        return ax

    def plot(self):
        """Plot the figure."""
        title = ''
        from pprint import pprint
        pprint(self.data)
        for _, timezone_set in enumerate(self.data):
            title = f"From {timezone_set['start']} to {timezone_set['end']}"
            name = f"{timezone_set['start'].strftime('%Y_%m_%d')}_to_{timezone_set['end'].strftime('%Y_%m_%d')}"
            path = os.path.join(self.path, name)

            ax = self.get_ax(timezone_set['set'])
            handles, labels = ax.get_legend_handles_labels()
            new_handles = [patches.Patch(color='green', label='Possible countries in time window.')]
            new_labels = ['Possible countries in time window.']
            handles += new_handles
            labels += new_labels
            ax.legend(handles, labels)
            fig = ax.get_figure()
            fig.set_figheight(40)
            fig.set_figwidth(80)

            fig.suptitle(title, fontsize=30)
            fig.savefig(path)

            plt.close(fig)

        return
