from __future__ import print_function
import re
import errno
import os
from glob import glob
from os.path import join, basename, splitext
from os import environ, remove
from shutil import copy, rmtree
from uuid import uuid4
import gzip
from configparser import ConfigParser
from datetime import date, timedelta
import subprocess


def gz(src, dest):
    """ Compresses a file to *.gz

        Parameters
        ----------
        src: filepath of file to be compressesd
        dest: destination filepath

    """

    filename = splitext(basename(src))[0]
    destpath = join(dest, '{}.gz'.format(filename))

    blocksize = 1 << 16     #64kB

    with open(src) as f_in:
        f_out = gzip.open(destpath, 'wb')
        while True:
            block = f_in.read(blocksize)
            if block == '':
                break
            f_out.write(block)
        f_out.close()


def aws_sync(src, dest):
    """ Synchronise a local directory to aws

    Parameters
    ----------
    src: local path
    dest: aws bucket

    """
    cmd = 'aws s3 sync {} {}'.format(src, dest)
    push = subprocess.call(cmd, shell=True)


def today():
    """ Returns a string format of today's date """
    return date.today().strftime('%Y%m%d')


def fwe():
    """ Returns a string format of the next friday's date """
    d = date.today()
    while d.weekday() != 4:
        d += timedelta(1)
    return d


def regex_match(string, pattern):
    """ Returns if there is a match between parameter and regex pattern """
    pattern = re.compile(pattern)
    return pattern.match(string)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def aws_bkup(section, include, exclude, s3root, categorize_weekly=True, compress=True, remove_source=True):
    """ Transfers a backup of any local files matching the user's criteria to AWS.

    Parameters
    ----------
    include: regex pattern to use for the file inclusion(s)
    exclude: regex pattern to use for the file exclusion(s)
    s3root: AWS root in which to send the backup
    categorize_weekly: switch between daily and weekly folder groupings
    compress: switch to compress outbound files to AWS

    """

    folder = '{}'.format(fwe() if categorize_weekly else today())
    tmp_root = join('/tmp', str(uuid4()))
    tmp_dir = join(tmp_root, folder)

    mkdir_p(tmp_dir)

    for file in glob(include):

        if regex_match(file, exclude):
            continue

        print('Processing: {}'.format(file))

        if compress:
            gz(file, tmp_dir)
        else:
            copy(file, tmp_dir)

        if remove_source:
            remove(file)

    aws_dest = join(s3root, section)

    print('Syncronizing {} to s3'.format(tmp_dir))
    aws_sync(tmp_root, aws_dest)

    if os.path.exists(tmp_root):
        rmtree(tmp_root)

    print('Done')


if __name__ == "__main__":
  
    import sys
    args = sys.argv

    if len(args) < 2:
        print("Usage: python -m aws-bkup /path/to/config.cfg")
        sys.exit()

    config = ConfigParser()
    config.read(args[1])

    environ['AWS_ACCESS_KEY_ID'] = config.get('aws', 'access_id')
    environ['AWS_SECRET_ACCESS_KEY'] = config.get('aws', 'secret_key')
    environ['AWS_DEFAULT_REGION'] = config.get('aws', 'region')

    for section in config.sections():
        if section != 'aws':
            print('Starting {}'.format(section))
            aws_bkup(
                section,
                config.get(section, 'include'),
                config.get(section, 'exclude'),
                config.get('aws', 's3root'),
                config.getboolean(section, 'categorize_weekly'),
                config.getboolean(section, 'compress'),
                config.getboolean(section, 'remove_source')
            )

