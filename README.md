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
region = us-east-1
path = /path/to/aws/binary

[category/subcategory]
include = /path/to/files/*.txt
exclude = ^.*sys.*$
compress = 1
categorize_weekly = 1
remove_source = 0
file_suffix = serv04

```

## Description:

Based on the above configuration file, all files matching the `include` glob will be processed.

The files will be moved to a temporary directory, optionally compressed and placed into a folder representing either the current date or friday week ending depending upon user preference.

Finally, the source files are optionally removed from the host.

## Run-Once

In addition to a scheduled (daily, weekly) run, a user may wish to run a specific backup periodically.

Users can override the `remove_source` specified in the configuration file, and additionally specify a subset of the
`sections` in which to perform the backup run. This will provide finer granularity over the backup than the default
usecase.

For example, the below call overrides the `remove_source` setting configured in the config, and runs backups for sections user_category1 and user_category5

```
$ python -m aws_backup /path/to/config --preserve_source --sections=user_category1,user_category5
```

## Requires

*NIX based system, python 2.7+, aws-cli.
