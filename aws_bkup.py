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


def gz(src, dest, file_suffix):
    """ Compresses a file to *.gz

        Parameters
        ----------
        src: filepath of file to be compressesd
        dest: destination filepath

    """

    filename = '{}-{}.gz'.format(splitext(basename(src))[0], file_suffix)
    destpath = join(dest, filename)

    blocksize = 1 << 16     #64kB

    with open(src) as f_in, gzip.open(destpath, 'wb') as f_out:
        while True:
            block = f_in.read(blocksize)
            if block == '':
                break
            f_out.write(block.encode())
  
    return filename


def cp(src, dest, file_suffix):

    filename_portioned = splitext(basename(src));
    filename = '{}-{}{}'.format(filename_portioned[0], file_suffix, filename_portioned[1])

    copy(src,dest)

    return basename(src) 

def aws_cp(src, dest, env):
    """ Synchronise a local directory to aws

    Parameters
    ----------
    src: local path
    dest: aws bucket

    """
    cmd = ['aws', 's3', 'cp', src, dest]

    errorcode = -1
    attempts = 0;

    while(errorcode != 0 and attempts < 3):
      errorcode = subprocess.call(cmd, env=env)

    return errorcode


def today():
    """ Returns a string format of today's date """
    return date.today().strftime('%Y%m%d')


def fwe():
    """ Returns a string format of the next friday's date """
    d = date.today()
    while d.weekday() != 4:
        d += timedelta(1)
    return d


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def aws_bkup(section, include, exclude, s3root, suffix, categorize_weekly=True, compress=True, remove_source=True, env=None):
    """ Transfers a backup of any local files matching the user's criteria to AWS.

    Parameters
    ----------
    include: regex pattern to use for the file inclusion(s)
    exclude: regex pattern to use for the file exclusion(s)
    s3root: AWS root in which to send the backup
    categorize_weekly: switch between daily and weekly folder groupings
    compress: switch to compress outbound files to AWS

    """

    print('Starting {}'.format(section))

    folder = '{}'.format(fwe() if categorize_weekly else today())
    tmp_root = join('/tmp', str(uuid4()))
    tmp_dir = join(tmp_root, folder)

    mkdir_p(tmp_dir)

    aws_dest = join(s3root, section, folder)

    exclude_pattern = re.compile(exclude)

    for file in glob(include):
        
        if exclude_pattern.match(file):
            continue

        print('Processing: {}'.format(file))

        if compress:
            copied_file = gz(file, tmp_dir, suffix)
        else:
            copied_file = cp(file, tmp_dir, suffix)

        error = aws_cp(
            join(tmp_dir, copied_file), 
            join(aws_dest, copied_file),
            env
        ) 

        remove(
            join(tmp_dir, copied_file)
        )

        # only remove if aws copy was successful
        if remove_source and not error > 0:
            try:
              remove(file)
            except OSError as e: 
              if e.errno != errno.ENOENT:
                raise


    if os.path.exists(tmp_root):
        rmtree(tmp_root)

    print('Done {}'.format(section))


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
            aws_bkup(
                section,
                config.get(section, 'include'),
                config.get(section, 'exclude'),
                config.get('aws', 's3root'),
                config.get(section, 'file_suffix'),
                config.getboolean(section, 'categorize_weekly'),
                config.getboolean(section, 'compress'),
                config.getboolean(section, 'remove_source'),
                {
                'AWS_ACCESS_KEY_ID': config.get('aws','access_id'),
                'AWS_SECRET_ACCESS_KEY': config.get('aws','secret_key'),
                'AWS_DEFAULT_REGION': config.get('aws','region'),
                'PATH': config.get('aws','path'),
                }
            )

