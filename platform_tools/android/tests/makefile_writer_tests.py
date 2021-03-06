#!/usr/bin/python

# Copyright 2014 Google Inc.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Test makefile_writer.py
"""

import argparse
import os
import shutil
import sys
import tempfile
import test_variables
import unittest

sys.path.append(test_variables.GYP_GEN_DIR)

import makefile_writer
import vars_dict_lib

EXPECTATIONS_DIR = os.path.join(os.path.dirname(__file__), 'expectations')
MAKEFILE_NAME = 'Android.mk'

def generate_dummy_vars_dict(name):
  """Create a VarsDict and fill it with dummy entries.

  Args:
      name: string to be appended to each entry, if not None.

  Returns:
      A VarsDict with dummy entries.
  """
  vars_dict = vars_dict_lib.VarsDict()
  for key in vars_dict.keys():
    entry = key.lower()
    if name:
      entry += '_' + name
    vars_dict[key].add(entry)
  return vars_dict


def generate_dummy_vars_dict_data(name, condition):
  """Create a dummy VarsDictData.

  Create a dummy VarsDictData, using the name for both the contained
  VarsDict and the VarsDictData

  Args:
      name: name used by both the returned VarsDictData and its contained
          VarsDict.
      condition: condition used by the returned VarsDictData.

  Returns:
      A VarsDictData with dummy values, using the passed in info.
  """
  vars_dict = generate_dummy_vars_dict(name)

  return makefile_writer.VarsDictData(vars_dict=vars_dict, name=name,
                                      condition=condition)


def generate_dummy_makefile(target_dir):
  """Create a dummy makefile to demonstrate how it works.

  Use dummy values unrelated to any gyp files. Its output should remain the
  same unless/until makefile_writer.write_android_mk changes.

  Args:
      target_dir: directory in which to write the resulting Android.mk
  """
  common_vars_dict = generate_dummy_vars_dict(None)

  deviation_params = [('foo', 'COND'), ('bar', None)]
  deviations = [generate_dummy_vars_dict_data(name, condition)
                for (name, condition) in deviation_params]

  makefile_writer.write_android_mk(target_dir=target_dir,
                                   common=common_vars_dict,
                                   deviations_from_common=deviations)


class MakefileWriterTest(unittest.TestCase):

  def test_write_group_empty(self):
    f = tempfile.TemporaryFile()
    assert f.tell() == 0
    for empty in (None, []):
      for truth in (True, False):
        makefile_writer.write_group(f, 'name', empty, truth)
        self.assertEqual(f.tell(), 0)
    f.close()

  def __compare_files(self, actual_name, expectation_name, msg=None):
    """Check that two files are identical.

    Assert line by line that the files match.

    Args:
        actual_name: Full path to the test file.
        expectation_name: Basename of the expectations file within which
            to compare. The file is expected to be in
            platform_tools/android/tests/expectations.
        msg: Message to pass to assertEqual.
    Raises:
        AssertionError: If the files do not match.
    """
    with open(actual_name, 'r') as result:
      with open(os.path.join(EXPECTATIONS_DIR,
                             expectation_name)) as expectation:
        for line in result:
          self.assertEqual(line, expectation.readline(), msg)

  def test_write_group(self):
    animals = ('dog', 'cat', 'mouse', 'elephant')
    fd, filename = tempfile.mkstemp()
    with open(filename, 'w') as f:
      makefile_writer.write_group(f, 'animals', animals, False)
    os.close(fd)
    # Now confirm that it matches expectations
    self.__compare_files(filename, 'animals.txt')

    with open(filename, 'w') as f:
      makefile_writer.write_group(f, 'animals_append', animals, True)
    # Now confirm that it matches expectations
    self.__compare_files(filename, 'animals_append.txt')
    os.remove(filename)

  def test_write_local_vars(self):
    vars_dict = generate_dummy_vars_dict(None)

    # Call variations of write_local_vars.
    for append in [ True, False ]:
      for name in [ None, 'arm', 'foo' ]:
        # Now write to a temporary file.
        fd, outfile = tempfile.mkstemp()
        with open(outfile, 'w') as f:
          makefile_writer.write_local_vars(f, vars_dict, append, name)
        os.close(fd)

        # Compare to the expected file.
        filename = 'write_local_vars'
        if append:
          filename += '_append'
        else:
          filename += '_no_append'
        if name:
          filename += '_' + name
        else:
          filename += '_no_name'
        self.__compare_files(outfile, filename)

        # KNOWN_TARGETS is always a part of the input VarsDict, but it should
        # not be written to the resulting file.
        # Note that this assumes none of our dummy entries is 'KNOWN_TARGETS'.
        known_targets_name = 'KNOWN_TARGETS'
        self.assertEqual(len(vars_dict[known_targets_name]), 1)

        with open(outfile, 'r') as f:
          self.assertNotIn(known_targets_name, f.read())
        os.remove(outfile)

  def test_write_android_mk(self):
    outdir = tempfile.mkdtemp()
    generate_dummy_makefile(outdir)

    self.__compare_files(os.path.join(outdir, MAKEFILE_NAME), MAKEFILE_NAME,
                         'If you\'ve modified makefile_writer.py, run ' +
                         '"makefile_writer_tests.py --rebaseline" ' +
                         'to rebaseline')

    shutil.rmtree(outdir)


def main():
  loader = unittest.TestLoader()
  suite = loader.loadTestsFromTestCase(MakefileWriterTest)
  results = unittest.TextTestRunner(verbosity=2).run(suite)
  print repr(results)
  if not results.wasSuccessful():
    raise Exception('failed one or more unittests')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-r', '--rebaseline',
                      help='Rebaseline expectation for Android.mk',
                      action='store_true')
  args = parser.parse_args()

  if args.rebaseline:
    generate_dummy_makefile(EXPECTATIONS_DIR)
  else:
    main()

