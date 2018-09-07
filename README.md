# Gitalizer

Gitalizer was created in the scope of my bachelor's thesis [Privacy implications of exposing Git metadata](https://github.com/Nukesor/thesis/blob/master/thesis/thesis.pdf).
The goal of this project is to explore the possible malicious usages of metadata that is collected during common Git usage.

This program is a combination of the Git/Github data aggregator `Gitalizer` and the analysis tool [Gitalysis](https://github.com/Nukesor/gitalysi://github.com/Nukesor/gitalysis).

Gitalysis can be capable of:
- Tracking the location of a targeted git user via their open source contributions.
- Detect holiday and sick leave in your commit pattern as well as other anomalies.
- Draw punchcards in the old Github style, which provide insight into the sleeping and working rhythm of a person.

It needs to be said again, that this project happened during the course of 5 months whilst writing my bachelor thesis.
I'm not all that familiar with modern data mining techniques and im very certain, that an experienced data scientist could extract quite sensitive information from this data.

The aggregation code of Gitalizer is quite stable and capable collecting several million commits in the course of a day.

This program is not written to be used in a malicious way! Please just don't do it.
I rather want people to understand, that somebody else might use it this way and that they might even be already doing it.
I want you to understand, that even simple metadata such as git commit timestamps and the git commit history can be used in malicious ways.

## Results:

Image from home location and travel path analysis:
<p align="center">
    <img src="https://raw.githubusercontent.com/Nukesor/images/master/gitalizer_map.png">
</p>

Holiday/sick leave and other anomaly analysis:
<p align="center">
    <img src="https://raw.githubusercontent.com/Nukesor/images/master/gitalizer_holiday.png">
</p>

Sleep rhythm and working hour analysis:
<p align="center">
    <img src="https://raw.githubusercontent.com/Nukesor/images/master/gitalizer_punchcard.png">
</p>

## Installation:

First of all several dependencies are needed. These are mostly required for analysis:
1. proj
2. geos
3. agg

You can install `gitalizer` and `gitalysis` either by using pip

    pip install gitalizer gitalysis


or by installing it manually:

- Clone the repositories
- (Optional) Create a virtual environment and activate it.
- Run `python setup.py install` for release mode or `python setup.py develop`, if you want to develop.

### Post install
- Setup PostgreSQL and create a database.
- Either copy the gitalizer.example.ini to your `~/./config/ ` directory or start `gitalizer` once to initialize a dummy config.
- Adjust all parameters to your needs.

## Cli
**DB** related:
- `gitalizer db initdb` Initializes a new database with schema and populates the timezone database
- `gitalizer db build_time_db` Rebuild the timezone database (needed if a new version was released)

**Scanning**:

*User*:
- `gitalizer scan user [login] --with-followers` Scan all repositories and stars of a user. If the `--with-followers` flag is provided, all repositories and stars of all followers and following will be scanned as well.

*Repository*:
- `gitalizer scan repository from_github [owner] [name]` Scan an repository by owner and name.
- `gitalizer scan repository from_github_for_users [full_name]` Scan all users of an github repository.

*Organization*:
- `gitalizer scan organization by_name [name]` Scan an organization by name.
- `gitalizer scan organization members [name]` Scan all members of an organization.
- `gitalizer scan organization user_membership` Get the associated organizations of all members in our database.

**Deletion** of entities:
- `gitalizer delete repository [full_name]` Delete a repository with all it's commit

**Maintenance** stuff:
- `gitalizer maintenance complete` Complete repositories which haven't been completely scanned, either due to an error or manual stopping.
- `gitalizer maintenance update` Rescan all repositories and users.
- `gitalizer maintenance clean` Remove duplicated commits. This is mostly probably deprecated functionality, since these problems shouldn't occur any longer, but it is left for possible future development problems.



# Interesting features:
- Flag contributors and repositories as explicitly scanned to avoid constant data growth during rescans.
- More deletion methods for other entities.
