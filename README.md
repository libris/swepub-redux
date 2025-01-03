# Swepub

Swepub consists of two programs

1. A pipeline, which fetches and cleans up publication metadata from a set of sources, using OAI-PMH. From this data an sqlite3 database is created which serves as the source for the service (the other program).
1. A service, the "Swepub website", which makes the aggregate Swepub data available for analysis.

## Setup

To set the system up, clone this repo, create a Python virtual env and install required Python packages:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

(Note that at the moment only Python 3.7 and 3.8 have been used for this project. Later versions may also work.)

### Setup: Annif

For automated subject classification we use [Annif](https://annif.org/). This is optional in the default DEV environment;
if Annif is not detected, autoclassification will be automatically disabled.
To set it up, follow the instructions in https://github.com/libris/swepub-annif.

## Pipeline

To run the pipeline and harvest a few sources do:

```bash
python3 -m pipeline.harvest --update --skip-unpaywall mdh miun mau
```

(`--skip-unpaywall` avoids hitting a non-public Unpaywall mirror; alternatively, you could set `SWEPUB_SKIP_REMOTE` which skips both Unpaywall and other remote services (e.g. shortdoi.org, issn.org).)

Expect this to take a few minutes. If you don't specify source(s) you instead get the full production data which takes a lot longer (~8 hours). Sources must exist in `pipeline/sources.json`. If the database doesn't exist, it will be created; if it already exists, sources will be incrementally updated (harvesting records added/updated/deleted since the previous execution of `pipeline.harvest --update`).

To forcibly create a new database, run `python3 -m pipeline.harvest --force` (or `-f`).

Run `python3 -m pipeline.harvest -h` to see all options. 

There are no running "services", nor any global state. Each time the pipeline is executed, an sqlite3 database is either created or updated. You may even run more than one harvester (with a different database path) in parallel if you like.

You can `purge` (delete) one or more sources. In combination with a subsequent `update` command, this lets you completely remove a source and then harvest it fully, while keeping records from other sources in the database intact:

```bash
python3 -m pipeline.harvest --purge uniarts
python3 -m pipeline.harvest --update uniarts
```

(If you omit the source name, all sources' records will be purged and fully harvested.)

For sources that keep track of deleted records, a much quicker way is:

```bash
python3 -m pipeline.harvest --reset-harvest-time uniarts
python3 -m pipeline.harvest --reset-harvest-time uniarts
```

`--reset-harvest-time` removes the `last_harvest` entry for the specified source(s), meaning the next `--update` will trigger a full harvest.

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
npm ci --prefix service/vue-client/
yarn --cwd service/vue-client/ build
```

For development, you can run `yarn --cwd service/vue-client/ build --mode=development` instead; this lets you use e.g. Vue Devtools.

To start the Swepub service (which provides the API and serves the static frontend files, if they exist):

```bash
# Make sure you're in the virtualenv created above
python3 -m service.swepub
```

Then visit http://localhost:5000. API docs are available on http://localhost:5000/api/v2/apidocs.

To use port other than 5000, set `SWEPUB_SERVICE_PORT`.


## Training/updating Annif
See https://github.com/libris/swepub-annif


## Tests

Unit tests:

```bash
# Make sure you're in the virtualenv created above
pytest

# Also test embedded doctests:
pytest --doctest-modules
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

You can also download only specific records (and when downloading specific records,
the XML will be pretty-printed):

```bash
python3 -m misc.fetch_records oai:DiVA.org:uniarts-1146 oai:DiVA.org:lnu-108145
```


## Testing XML->JSON-LD conversion

Having downloaded the XML of a record (see "Working with local XML files" above):
```bash
python3 -m misc.fetch_records oai:DiVA.org:uniarts-1146
```

...you can then test conversion from Swepub MODS XML to KBV/JSON-LD like so:


```bash
python3 -m misc.mods_to_json resources/mods_to_xjsonld.xsl _xml/uniarts/oaiDiVA.orguniarts-1146.xml
```

Then you can edit `resources/mods_to_xjsonld.xsl` and/or `_xml/uniarts/oaiDiVA.orguniarts-1146.xml`,
run `misc.mods_to_json` again, and see what happens.

(With `xsltproc` you can also see the intermediary post-XSLT, pre-JSON-conversion XML:
`xsltproc resources/mods_to_xjsonld.xsl _xml/uniarts/oaiDiVA.orguniarts-1146.xml`)

## Testing conversion, enrichment and "legacy" export pipeline

```bash
python3 -m misc.testpipe _xml/sometestfile.xml /tmp/swepub-testpipe/
```
Produces 3 files corresponding to conversion, audit and legacy steps:
```bash
/tmp/swepub-testpipe/sometestfile-out-1.jsonld
/tmp/swepub-testpipe/sometestfile-out-2-audited.jsonld
/tmp/swepub-testpipe/sometestfile-out-3-legacy.jsonld
```

## Testing changes to Swepub "legacy" export

Install `mysql-server` or `mariadb-server`. Follow the instructions in `pipeline/legacy_sync.py`.
Then, if you've set the relevant env vars (`SWEPUB_LEGACY_SEARCH_USER`, etc.), `pipeline.harvest`
will update the MySQL database. You can then inspect the JSON data of a specific record:

```bash
mysql -u<user> -p<password> swepub_legacy -sN -e "select data from enriched where identifier = 'oai:DiVA.org:uniarts-1146';" | jq
```

## Updating Resources

Some resources are generated from external data, and may eventually become stale and in need of a refresh. See `resources/Makefile`.
