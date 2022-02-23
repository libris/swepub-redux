# Swepub

Swepub consists of two programs

1. A pipeline, which fetches and cleans up publication metadata from a set of sources, using OAI-PMH. From this data an sqlite3 database is created which serves as the source for the service (the other program).
1. A service, the "Swepub website", which makes the aggregate Swepub data available for analysis.

## Setup

To set the system up (for local development), create a Python virtual env and install required Python packages:
```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

(Note that at the moment only Python 3.6 and 3.7 has been used for this project, later versions may also work)

## Pipeline

To run the pipeline and harvest a few sources do:

```bash
$ python3 pipeline/harvest.py --update mdh miun mau
```

Expect this to take a few minutes. If you don't specify source(s) you instead get the full production data which takes a lot longer. Sources must exist in `pipeline/sources.json`. If the database doesn't exist, it will be created; if it already exists, sources will be incrementally updated (harvesting records added/updated/deleted since the previous execution of `harvest.py --update`).

To forcibly create a new database, run `python3 pipeline/harvest.py --force` (or `-f`).

Run `python3 pipeline/harvest.py` to see all options. 

There are no running "services". Each time the pipeline is executed, an sqlite3 database is either created or updated. You may even run more than one `harvest.py` (with a different database path) in parallel if you like.

You can `purge` (delete) one or more sources. In combination with a subsequent `update` command, this lets you completely remove a source and then harvest it fully, while keeping records from other sources in the database intact:

```bash
$ python3 pipeline/harvest.py --purge uniarts
$ python3 pipeline/harvest.py --update uniarts
```

(If you omit the source name, all sources' records will be purged and fully harvested.)

The resulting sqlite3 database has roughly the following structure (see storage.py for details):

| Table | Description |
| --- | --- |
|original| Original XML data for every harvested record. |
|converted| Converted+validated+normalized versions of each record. There is foreign key for each row which references the 'original' table |
|cluster| Clusters of converted records that are all considered to be duplicates of the same publication. There is a foreign key which references the 'converted' table. |
|finalized| A union or "master" record for each cluster, containing a merger of all the records in the cluster. There is a foreign key which references the 'cluster' table. |


## Service

If you want the frontend, make sure Nodejs/npm/yarn are installed, and then:

```bash
npm install --prefix service/vue-client/
yarn --cwd service/vue-client/ build
```

To start the Swepub service (which provides the API and serves the static frontend files, if they exist):

```bash
python3 service/swepub.py
```
