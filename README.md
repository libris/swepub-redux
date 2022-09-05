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

(Note that at the moment only Python 3.7 and 3.8 have been used for this project, later versions may also work)

## Pipeline

To run the pipeline and harvest a few sources do:

```bash
$ python3 -m pipeline.harvest --update --skip-unpaywall mdh miun mau
```

Expect this to take a few minutes. If you don't specify source(s) you instead get the full production data which takes a lot longer (~8 hours). Sources must exist in `pipeline/sources.json`. If the database doesn't exist, it will be created; if it already exists, sources will be incrementally updated (harvesting records added/updated/deleted since the previous execution of `pipeline.harvest --update`).

To forcibly create a new database, run `python3 -m pipeline.harvest --force` (or `-f`).

Run `python3 -m pipeline.harvest -h` to see all options. 

There are no running "services", nor any global state. Each time the pipeline is executed, an sqlite3 database is either created or updated. You may even run more than one harvester (with a different database path) in parallel if you like.

You can `purge` (delete) one or more sources. In combination with a subsequent `update` command, this lets you completely remove a source and then harvest it fully, while keeping records from other sources in the database intact:

```bash
$ python3 -m pipeline.harvest --purge uniarts
$ python3 -m pipeline.harvest --update uniarts
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
# Make sure you're in the virtualenv created above
python3 -m service.swepub
```

Then visit http://localhost:5000. API docs are available on http://localhost:5000/api/v1/apidocs.


## Tests

Unit tests:

```bash
# Make sure you're in the virtualenv created above
pytest
```

To harvest specific test records, first start the mock API server:

```bash
python3 -m tests.mock_api
```

Then, in another terminal:

```bash
export SWEPUB_SOURCE_FILE=tests/sources_test.json
python3 -m pipeline.harvest -f dedup
python3 -m service.swepub
```

To add a new test record, for example `foobar.xml`:

First, add `foobar.xml` to `tests/test_data`

Then, edit `tests/sources_test.json` and add an entry for the file:

```json
  "foobar": {
    "code": "whatever",
    "name": "TEST - whatever",
    "sets": [
      {
        "url": "http://localhost:8549/foobar",
        "subset": "SwePub-whatever",
        "metadata_prefix": "swepub_mods"
      }
    ]
  }
 ```

Make sure `foobar` in `url` corresponds to the filename (minus the `.xml` suffix).

Now you should be able to harvest it:

```bash
# Again, make sure the mock API server is rnning and that you've set
# export SWEPUB_SOURCE_FILE=tests/sources_test.json
python3 -m pipeline.harvest -f foobar
```


## Working with local XML files

To quickly test changes without having to hit real OAI-PMH servers over and over,
you can download the XML files locally and start a local OAI-PMH server from which
you can harvest.


```bash
# Make sure you're in the virtualenv created above

# Harvest to disk
python3 -m misc.fetch_records uniarts ths # Saves to ./_xml by default; -h for options
# _or_, to fetch all sources: python3 -m misc.fetch_records

# Start OAI-PMH server in the background or in another terminal
python3 -m misc.oai_pmh_server # See -h for options

# Now harvest (--local-server defaults to http://localhost:8383/oai)
python3 -m pipeline.harvest -f uniarts ths --local-server
```

This "OAI-PMH server" supports only the very bare minimum for `pipeline.harvest` to work
in (non-incremental mode). Remember that if you run `misc.fetch_records` again, you need
to restart `misc.oai_pmh_server` for it to pick up the changes.
