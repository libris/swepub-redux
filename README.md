# SwePub

SwePub consists of two programs

1. A pipeline, which fetches and cleans up publication metadata from a set of sources, using OAI-PMH. From this data an sqlite3 database is created which serves as the source for the service (the other program).
1. A service, the "swepub website", which makes the aggregate swepub data available for analysis.

## Setup

To set the system up (for local development), create a Python virtual env and do:
```
$ pip install -r requirements.txt
```

(Note that at the moment only Python 3.7 has been used for this project, later versions may also work)

## Pipeline

To run the pipeline do:

```
$ python3.7 pipeline/harvest.py devdata
```

Expect this to take a few minutes. If you omit the "devdata" parameter you instead get the full production data which takes 5 or 6 hours.

There is no state to be considered here and no running "services". Each time the pipeline is executed a new sqlite3 database is produced as output. You may even run more than one in parallell if you like.

The resulting sqlite3 database has roughly the following structure (see storage.py for details):

| Table | Description |
| --- | --- |
|original| XML data for every harvested record unchanged. These are kept only because the swepub API exposes them under "/original". |
|converted| Converted+validated+normalized versions of each record, foreign key for each row references the 'original' table |
|cluster| Clusters of converted records that are all considered to be duplicates of the same publication, contains foreign key rowids into the 'converted' table. |
|finalized| A union or "master" record for each cluster, containing a merger of all the records in the cluster. foreign key references which cluster the union record is for. |


## Service

Not yet carried over from the old swepub code.