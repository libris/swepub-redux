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

To run the pipeline do:

```bash
$ python3 pipeline/harvest.py devdata
```

Expect this to take a few minutes. If you omit the "devdata" parameter you instead get the full production data which takes a lot longer. You can also specify one or more individual source(s) (these must exist in `pipeline/sources.json`), e.g.:

```
$ python3 pipeline/harvest.py ths uniarts
```

There is no state to be considered here and no running "services". Each time the pipeline is executed a new sqlite3 database is produced as output. You may even run more than one in parallel if you like. As an option you can if you wish update an existing database with whatever new data is available by using the parameter `update`:

```bash
$ python3 pipeline/harvest.py update # update all sources
$ python3 pipeline/harvest.py update uniarts ths # update specific sources
```

You can `purge` (delete) one or more sources. In combination with a subsequent `update` command, this lets you completely remove a source and then harvest it fully, while keeping records from other sources in the database intact:

```bash
$ python3 pipeline/harvest.py purge uniarts
$ python3 pipeline/harvest.py update uniarts
```

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
