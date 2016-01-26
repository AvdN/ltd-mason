"""Test ltdmason.manifest."""

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
from builtins import *
from future.standard_library import install_aliases
install_aliases()

import pkg_resources
import pytest

from ltdmason.manifest import Manifest


@pytest.fixture
def demo_science_pipelines_manifest():
    resource_args = (__name__, 'demo_science_pipelines_manifest.yaml')
    assert pkg_resources.resource_exists(*resource_args)
    yaml_data = pkg_resources.resource_string(*resource_args)
    return yaml_data


@pytest.mark.xfail
def test_manifest_roundtrip(demo_science_pipelines_manifest):
    # Can't get perfect round-trip equality of the YAML
    manifest = Manifest(demo_science_pipelines_manifest)
    assert manifest.yaml == demo_science_pipelines_manifest


def test_manifest_parse(demo_science_pipelines_manifest):
    manifest = Manifest(demo_science_pipelines_manifest)
    assert manifest.data['refs'][0] == 'master'
    assert 'url' in manifest.data['doc_repo']
    assert 'ref' in manifest.data['doc_repo']
    assert 'afw' in manifest.data['packages']
    assert 'dirname' in manifest.data['packages']['afw']
    assert 'url' in manifest.data['packages']['afw']
    assert 'ref' in manifest.data['packages']['afw']


def test_doc_repo_data(demo_science_pipelines_manifest):
    manifest = Manifest(demo_science_pipelines_manifest)
    assert 'pipelines_docs' == manifest.doc_repo_name
    assert 'master' == manifest.doc_repo_ref
    assert 'https://github.com/lsst-sqre/pipelines_docs.git' \
        == manifest.doc_repo_url