#!/usr/bin/env python
"""Tests for ltdmason.s3upload.

   These tests required the following environment variables:

   ``LTD_MASON_TEST_AWS_ID``
      AWS access key ID

   ``LTD_MASON_TEST_AWS_SECRET``
      AWS secret access key

   ``LTD_MASON_TEST_BUCKET``
      Name of an S3 bucket that already exists and can be used for testing.

   The tests will be skipped if they are not available.

   Note that this test will create a random uuid4) directory at the root of
   ``LTD_MASON_TEST_BUCKET``, though the test harness will attempt to delete
   it.
"""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
from builtins import *  # NOQA
from future.standard_library import install_aliases
install_aliases()

import os
import shutil
import tempfile
import uuid
import logging

import pytest
import boto3
from ltdmason import s3upload

log = logging.getLogger(__name__)


@pytest.mark.skipif(os.getenv('LTD_MASON_TEST_AWS_ID') is None or
                    os.getenv('LTD_MASON_TEST_AWS_SECRET') is None or
                    os.getenv('LTD_MASON_TEST_BUCKET') is None,
                    reason='Set LTD_MASON_TEST_AWS_ID, '
                           'LTD_MASON_TEST_AWS_SECRET and '
                           'LTD_MASON_TEST_BUCKET')
def test_s3upload(request):
    """Integration test of s3upload and synchronnization upon file deletes.

    This is a test that operates more as an integrations test than a unit
    test.
    """
    bucket_name = os.getenv('LTD_MASON_TEST_BUCKET')
    aws_credentials = {
        'aws_access_key_id': os.getenv('LTD_MASON_TEST_AWS_ID'),
        'aws_secret_access_key': os.getenv('LTD_MASON_TEST_AWS_SECRET')}
    session = boto3.session.Session(**aws_credentials)

    logging.basicConfig(level=logging.ERROR)

    logging.getLogger('ltdmason.s3upload').level = logging.INFO
    logging.getLogger(__name__).level = logging.INFO

    paths = [
        'file1.txt',
        'file2.txt',
        'dir1/file11.txt',
        'dir1/file12.txt',
        'dir1/dir11/file111.txt',
        'dir1/dir11/file112.txt',
        'dir2/file21.txt',
        'dir2/file22.txt',
    ]

    temp_dir = tempfile.mkdtemp()
    temp_bucket_dir = str(uuid.uuid4())

    def cleanup():
        print("Cleaning up the bucket")
        _clean_bucket(session, bucket_name, temp_bucket_dir)
    request.addfinalizer(cleanup)

    _create_test_files(temp_dir, paths)

    s3upload.upload(bucket_name,
                    temp_bucket_dir,
                    temp_dir,
                    **aws_credentials)
    _test_objects_exist(session, bucket_name, temp_bucket_dir, paths)

    # Remove some files (on filesystem and in path manifest)
    shutil.rmtree(os.path.join(temp_dir, 'dir1'))
    paths.remove('dir1/file11.txt')
    paths.remove('dir1/file12.txt')
    paths.remove('dir1/dir11/file111.txt')
    paths.remove('dir1/dir11/file112.txt')
    os.remove(os.path.join(temp_dir, 'file2.txt'))
    paths.remove('file2.txt')

    s3upload.upload(bucket_name,
                    temp_bucket_dir,
                    temp_dir,
                    **aws_credentials)
    _test_objects_exist(session, bucket_name, temp_bucket_dir, paths)

    shutil.rmtree(temp_dir)


def _create_test_files(temp_dir, file_list):
    for path in file_list:
        _write_file(temp_dir, path)


def _write_file(root_dir, rel_path):
    filepath = os.path.join(root_dir, rel_path)
    try:
        os.makedirs(os.path.dirname(filepath))
    except OSError:
        # probably exists; pickup real error on write
        pass

    with open(filepath, 'w') as f:
        f.write('Content of {0}'.format(os.path.basename(filepath)))


def _test_objects_exist(session, bucket_name, bucket_root, file_list):
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    bucket_objects = []
    for obj in bucket.objects.filter(Prefix=bucket_root):
        if obj.key.endswith('/'):
            continue
        bucket_objects.append(obj.key)

    assert len(bucket_objects) == len(file_list)
    for path in file_list:
        found = False
        for bucket_path in bucket_objects:
            if bucket_path.endswith(path):
                found = True
                continue
        if not found:
            log.error('{0} not found in bucket'.format(bucket_path))
            assert False


def _clean_bucket(session, bucket_name, root_path):
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)

    # Normalize directory path for searching patch prefixes of objects
    if not root_path.endswith('/'):
        root_path += '/'

    key_objects = [{'Key': obj.key}
                   for obj in bucket.objects.filter(Prefix=root_path)]
    if len(key_objects) == 0:
        return
    delete_keys = {'Objects': []}
    delete_keys['Objects'] = key_objects
    # based on http://stackoverflow.com/a/34888103
    s3.meta.client.delete_objects(Bucket=bucket.name,
                                  Delete=delete_keys)