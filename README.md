# aws-bkup

A utility to assist with the backup and removal of server-side log files.

Users can specify:

 * path(s) to backup
 * aws destination bucket (incl. additional trees)
 * optional compression
 * optional removal source file(s)

## Usage:
```
$ python -m aws_bkup path/to/config

```

## Configuration:
```
[aws]
access_id = 123
secret_key = 1234
s3root = s3://backup-bucket

[category/subcategory]
include = /path/to/files/*.txt
exclude = ^.*sys.*$
compress = 1
categorize_weekly = 1
remove_source = 0

```

## Description:

Based on the above configuration file, all files matching the `include` glob will be processed.

The files will be moved to a temporary directory, optionally compressed and placed into a folder representing either the current date or friday week ending depending upon user preference.

Finally, the source files are optionally removed from the host.

## Requires

*NIX based system, python 2.7+, aws-cli.
