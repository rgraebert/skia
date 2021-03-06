#!/usr/bin/python

# Copyright 2014 Google Inc.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Script for generating the Android framework's version of Skia from gyp
files.
"""

import android_framework_gyp
import os
import shutil
import sys
import tempfile

# Find the top of trunk
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
SKIA_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir,
                                         os.pardir))

# Find the directory with our helper files, and add it to the path.
GYP_GEN_DIR = os.path.join(SKIA_DIR, 'platform_tools', 'android', 'gyp_gen')
sys.path.append(GYP_GEN_DIR)

import gypd_parser
import makefile_writer
import vars_dict_lib

# Folder containing all gyp files and generated gypd files.
GYP_FOLDER = 'gyp'

# TODO(scroggo): Update the docstrings to match the style guide:
# http://google-styleguide.googlecode.com/svn/trunk/pyguide.html#Comments
def clean_gypd_files(folder):
  """
  Remove the gypd files generated by android_framework_gyp.main().
  @param folder Folder in which to delete all files ending with 'gypd'.
  """
  assert os.path.isdir(folder)
  files = os.listdir(folder)
  for f in files:
    if f.endswith('gypd'):
      os.remove(os.path.join(folder, f))

def generate_var_dict(target_dir, target_file, skia_arch_type, have_neon):
  """
  Create a VarsDict for a particular arch type. Each paramater is passed
  directly to android_framework_gyp.main().
  @param target_dir Directory containing gyp files.
  @param target_file Target gyp file.
  @param skia_arch_type Target architecture.
  @param have_neon Whether the target should build for neon.
  @return a VarsDict containing the variable definitions determined by gyp.
  """
  result_file = android_framework_gyp.main(target_dir, target_file,
                                           skia_arch_type, have_neon)
  var_dict = vars_dict_lib.VarsDict()
  gypd_parser.parse_gypd(var_dict, result_file)
  clean_gypd_files(target_dir)
  print '.',
  return var_dict

def main(target_dir=None):
  """
  Read gyp files and create Android.mk for the Android framework's
  external/skia.
  @param target_dir Directory in which to place 'Android.mk'. If None, the file
                    will be placed in skia's root directory.
  """
  # Create a temporary folder to hold gyp and gypd files. Create it in SKIA_DIR
  # so that it is a sibling of gyp/, so the relationships between gyp files and
  # other files (e.g. platform_tools/android/gyp/dependencies.gypi, referenced
  # by android_deps.gyp as a relative path) is unchanged.
  # Use mkdtemp to find an unused folder name, but then delete it so copytree
  # can be called with a non-existent directory.
  tmp_folder = tempfile.mkdtemp(dir=SKIA_DIR)
  os.rmdir(tmp_folder)
  shutil.copytree(os.path.join(SKIA_DIR, GYP_FOLDER), tmp_folder)

  try:
    main_gyp_file = 'android_framework_lib.gyp'

    print 'Creating Android.mk',

    # Generate a separate VarsDict for each architecture type.  For each
    # archtype:
    # 1. call android_framework_gyp.main() to generate gypd files
    # 2. call parse_gypd to read those gypd files into the VarsDict
    # 3. delete the gypd files
    #
    # Once we have the VarsDict for each architecture type, we combine them all
    # into a single Android.mk file, which can build targets of any
    # architecture type.

    # The default uses a non-existant archtype, to find all the general
    # variable definitions.
    default_var_dict = generate_var_dict(tmp_folder, main_gyp_file, 'other',
                                         False)
    arm_var_dict = generate_var_dict(tmp_folder, main_gyp_file, 'arm', False)
    arm_neon_var_dict = generate_var_dict(tmp_folder, main_gyp_file, 'arm',
                                          True)
    x86_var_dict = generate_var_dict(tmp_folder, main_gyp_file, 'x86', False)

    mips_var_dict = generate_var_dict(tmp_folder, main_gyp_file, 'mips', False)

    # Compute the intersection of all targets. All the files in the intersection
    # should be part of the makefile always. Each dict will now contain trimmed
    # lists containing only variable definitions specific to that configuration.
    var_dict_list = [default_var_dict, arm_var_dict, arm_neon_var_dict,
                     x86_var_dict, mips_var_dict]
    common = vars_dict_lib.intersect(var_dict_list)

    # Further trim arm_neon_var_dict with arm_var_dict. After this call,
    # arm_var_dict (which will now be the intersection) includes all definitions
    # used by both arm and arm + neon, and arm_neon_var_dict will only contain
    # those specific to arm + neon.
    arm_var_dict = vars_dict_lib.intersect([arm_var_dict, arm_neon_var_dict])

    # Now create a list of VarsDictData holding everything but common.
    deviations_from_common = []
    deviations_from_common.append(makefile_writer.VarsDictData(
        arm_var_dict, 'arm'))
    deviations_from_common.append(makefile_writer.VarsDictData(
        arm_neon_var_dict, 'arm', 'ARCH_ARM_HAVE_NEON'))
    deviations_from_common.append(makefile_writer.VarsDictData(x86_var_dict,
                                                               'x86'))
    # Currently, x86_64 is identical to x86
    deviations_from_common.append(makefile_writer.VarsDictData(x86_var_dict,
                                                               'x86_64'))

    deviations_from_common.append(makefile_writer.VarsDictData(mips_var_dict,
                                                               'mips'))

    makefile_writer.write_android_mk(target_dir=target_dir,
        common=common, deviations_from_common=deviations_from_common)

  finally:
    shutil.rmtree(tmp_folder)

if __name__ == '__main__':
  main()
