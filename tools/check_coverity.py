#!/usr/bin/env python3
#
# DDS Security library
# Copyright (c) 2018-2019, Arm Limited and Contributors. All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Wrapper to run Coverity on the project.
# Tested with version 2018.06.

import argparse
import os
import platform
import shutil
import subprocess
import sys
from utils import build_directory


def coverity_base_path():
    """
    Retrieve base directory where coverity is installed
    """
    cov_configure_path = shutil.which('cov-configure')
    if not cov_configure_path:
        return None

    path_bin = os.path.dirname(cov_configure_path)
    path_base = os.path.normpath('{}/../'.format(path_bin))
    return path_base


profiles = [
    {
        'name': 'standard',
        'desc': 'Standard checkers',
        'checkers':
            '  --aggressiveness-level=high'
            '  --all',
    },
    {
        'name': 'misra',
        'desc': 'Misra-C 2012 containing exceptions for this project',
        'checkers': '  --coding-standard-config {}/tools/misra.config'
            .format(os.getcwd()),
    },
    {
        'name': 'misra-strict',
        'desc': 'Strict Misra-C 2012 profile',
        'checkers':
            '  --coding-standard-config {}/config/MISRA/MISRA_c2012_7.config'
            .format(coverity_base_path() or "<path/to/coverity>"),
    },
]


def do_check_profile(profile, output_dir):
    """
    Run checkers on the base code as specified by the profile parameter.
    If output_dir is set, the reports (html and text) are saved in the
    specified directory.
    """

    print('*'*80)
    print("Checker: {}".format(profile['name']))
    print('*'*80)

    base_dir = os.path.abspath('..')

    # Analyze
    subprocess.check_call('cov-analyze'
                          '  --config ./coverity_config.xml'
                          '  --dir ./coverity_build' + profile['checkers'],
                          shell=True)

    # Generate html report
    subprocess.check_call('cov-format-errors'
                          '  --html-output {}/{}-html'
                          '  --filesort'
                          '  --file {}'
                          '  --dir ./coverity_build'
                          .format(output_dir, profile['name'], base_dir),
                          shell=True)

    # Generate text report
    filename = '{}/{}-report.txt'.format(output_dir, profile['name'])
    subprocess.check_call('cov-format-errors'
                          '  --emacs-style'
                          '  --filesort'
                          '  --file {}'
                          '  --dir ./coverity_build | tee {}'
                          .format(base_dir, filename),
                          shell=True)

    # If the text report is empty, there are no errors
    if os.stat(filename).st_size == 0:
        return 0
    else:
        return 1


def do_check(selected_profiles, output_base_dir, use_cross_compilation,
             selected_build_types):
    """
    Setup and build the project under the Coverity tools.
    Return 0 when the analysis succeeded. Any other value when the build fails
    or the code base has issues.
    """
    has_issues = False

    if use_cross_compilation:
        if 'CROSS_COMPILE' not in os.environ:
            print("Error: When using the cross-compiler option, you must set"
                  " the environment variable CROSS_COMPILE")
            sys.exit(1)
        compiler = os.environ.get('CROSS_COMPILE')+'gcc'
        print("Using cross compiler: {}".format(compiler))

    elif 'CC' in os.environ:
        cc = os.environ.get('CC')
        print("Using compiler from the CC: {}".format(cc))
        compiler = os.path.basename(cc)

    else:
        compiler = 'gcc'

    if os.path.dirname(compiler):
        print("Error: Coverity does not accept a full path to the compiler,"
              " you must only specify the executable name.")
        sys.exit(1)

    for build_type in selected_build_types:

        print('*'*80)
        print("Build type: {}".format(build_type))

        output_base_dir = 'coverity_results' if output_base_dir is None \
            else output_base_dir
        output_dir = os.path.join(output_base_dir, build_type)

        with build_directory():
            cmake_params = '-DCMAKE_BUILD_TYPE={}'.format(
                build_type.capitalize())

            if use_cross_compilation:
                cmake_params += \
                    ' -DCMAKE_TOOLCHAIN_FILE=../tools/toolchain.cmake'

            print("CMake parameters: {}".format(cmake_params))

            # Run cmake to prepare the build
            ret = subprocess.call('cmake {} ..'.format(cmake_params),
                                  shell=True)
            if ret != 0:
                return ret

            # Configure compiler for native compilation
            subprocess.check_call('cov-configure'
                                  '  --comptype gcc'
                                  '  --compiler {}'
                                  '  --config ./coverity_config.xml'
                                  '  --template'.format(compiler), shell=True)

            # Initialize Coverity build directory
            subprocess.check_call('cov-build'
                                  '  --config ./coverity_config.xml'
                                  '  --dir ./coverity_build'
                                  '  --initialize', shell=True)

            # Build library and trusted application
            ret = subprocess.call('cov-build'
                                  '  --config ./coverity_config.xml'
                                  '  --dir ./coverity_build'
                                  '  --capture make libddssec ta', shell=True)
            if ret != 0:
                return ret

            for profile_name in selected_profiles:
                profile = next(p for p in profiles
                               if profile_name == p['name'])
                result = do_check_profile(profile, output_dir)
                if result == 1:
                    has_issues = True

    if has_issues:
        return 1
    else:
        return 0


def main(argv=[], prog_name=''):
    print('DDS Security library Coverity Wrapper')
    parser = argparse.ArgumentParser(
        prog=prog_name,
        formatter_class=argparse.RawTextHelpFormatter)

    profile_list = ['all']
    profile_list += [p['name'] for p in profiles]

    build_type_list = ['release', 'debug']

    # Build profiles documentation
    profile_doc = '\n'
    for profile in profiles:
        profile_doc += '{} - {}:\n{}\n'.format(profile['name'],
                                               profile['desc'],
                                               profile['checkers'])

    parser.add_argument(
        '-b', '--build-type', choices=build_type_list,
        help='Build type.',
        required=False, default=build_type_list, nargs='+')

    parser.add_argument(
        '-c', '--cross-compile', action='store_true',
        dest='cross_compile',
        help='Use cross-compilation.',
        required=False)

    parser.add_argument(
        '-o', '--output-dir', action='store',
        help='Path to directory where the results are going to be stored.'
        ' By default, the results are discarded at the end of the checks.',
        default=None,
        required=False)

    parser.add_argument(
        '-p', '--profile', choices=profile_list,
        help='Each profile enables one or more checkers:' +
             profile_doc + '\'all\' checks all profiles',
        required=False, default=[profile_list[0]], nargs='+')

    args = parser.parse_args(argv)

    if args.output_dir is not None:
        output_dir = os.path.abspath(args.output_dir)
    else:
        output_dir = None

    selected_profiles = args.profile

    # Ensure 'all' is not being mixed with other profiles
    for profile in args.profile:
        if profile == 'all':
            if len(args.profile) > 1:
                print("Error: When using 'all', do not include any other "
                      "profile")
                return 1
            else:
                # When 'all' is used, replace it with all the profile names
                selected_profiles = [p['name'] for p in profiles]

    if not args.cross_compile:
        if platform.machine() == 'x86_64':
            print('Error: When building on a x86_64, your only option is '
                  'to use the parameter --cross-compile.')
            sys.exit(1)

    if coverity_base_path() is None:
        print("Error: Coverity was not found on your system. ")
        print("Ensure Coverity is installed and added to the environment "
              "variable $PATH.")
        sys.exit(1)

    return do_check(selected_profiles, output_dir, args.cross_compile,
                    args.build_type)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:], sys.argv[0]))
