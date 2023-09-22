import abc
import codecs
import collections
import contextlib
import copy
import copyreg
import dataclasses
import distutils
import enum
import functools
import importlib
import inspect
import linecache
import logging
import multiprocessing
import operator
import os
import posixpath
import random
import re
import selectors
import signal
import sre_compile
import sre_parse
import sys
import tempfile
import threading
import tokenize
import traceback
import types
import typing
import unittest
import uuid
import warnings
import weakref

import _collections_abc
import _weakrefset
import decorator
import google.protobuf
import numpy
import setuptools

import paddle

from ..utils import log


def _strip_init_py(s):
    return re.sub(r"__init__.py$", "", s)


def _module_dir(m: types.ModuleType):
    return _strip_init_py(m.__file__)


skip_file_names = {
    _module_dir(m)
    for m in (
        abc,
        collections,
        contextlib,
        copy,
        copyreg,
        dataclasses,
        enum,
        functools,
        google.protobuf,
        importlib,
        inspect,
        linecache,
        logging,
        multiprocessing,
        numpy,
        operator,
        os,
        posixpath,
        random,
        re,
        selectors,
        sre_compile,
        sre_parse,
        signal,
        tempfile,
        threading,
        tokenize,
        traceback,
        types,
        typing,
        unittest,
        weakref,
        _collections_abc,
        _weakrefset,
        decorator,
        codecs,
        uuid,
        setuptools,
        distutils,
        warnings,
    )
}


sot_path = os.path.dirname(__file__).rpartition("/")[0] + "/"
paddle_path = sys.modules["paddle"].__file__.rpartition("/")[0] + "/"

skip_file_names.add(sot_path)
skip_file_names.add(paddle_path)
skip_file_names.add(
    "<frozen importlib",
)
skip_file_names.add("<__array_function__ internals>")

skip_file_name_re = re.compile(
    f"^({'|'.join(map(re.escape, skip_file_names))})"
)

customed_skip_code = set()

no_skip_code = {paddle.nn.Sequential.forward.__code__}


def need_skip_path(filepath: str) -> bool:
    """
    Check if the file should be skipped and not transcribed.

    Args:
        filepath: The path of the file to check.

    Returns:
        bool: True if the file should be skipped.
    """
    if not filepath.startswith("<"):
        filepath = os.path.abspath(filepath)
    return bool(skip_file_name_re.match(filepath))


def skip_function(function):
    customed_skip_code.add(function.__code__)
    return function


def need_skip(frame):
    pycode = frame.f_code
    if pycode in no_skip_code:
        return False
    if pycode in customed_skip_code:
        log(3, f"Skip frame by code: {pycode}\n")
        return True
    filename = pycode.co_filename
    if sys.version_info >= (3, 11) and filename.startswith("<frozen"):
        # NOTE(SigureMo): In Python 3.11, the core modules essential for
        # Python startup are “frozen”. So we need get original filename from
        # frame.
        # see https://docs.python.org/3/whatsnew/3.11.html#faster-startup for more details.
        # This workaround is refer to pdb.py
        # https://github.com/python/cpython/blob/3.11/Lib/pdb.py#L1328-L1331
        _filename = frame.f_globals.get('__file__', None)
        if isinstance(_filename, str):
            filename = _filename
    return need_skip_path(filename)
