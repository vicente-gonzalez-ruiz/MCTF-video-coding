#!/usr/bin/env python3
# -*- coding: iso-8859-15 -*-


## @file texture_expand_hfb_ltw.py
#  Expand the HFB texture data, using LTW.
#  The two main steps performed are:
#  - Decode components and
#  - Multiplexing components (Y, U y V).
#
#  @authors Vicente Gonzalez-Ruiz.
#  @date Last modification: 2015, January 7.

## @package texture_expand_hfb_ltw
#  Expand the HFB texture data, using LTW.
#  The two main steps performed are:
#  - Decode components and
#  - Multiplexing components (Y, U y V).

import sys
import os
from subprocess import check_call
from subprocess import CalledProcessError
import arguments_parser

## File that contains the HFB data.
file = ""
## Number of pictures to process.
pictures = 33

## The parser module provides an interface to Python's internal parser
## and byte-code compiler.
parser = arguments_parser(description="Expands the the HFB texture data using LTW.")
parser.add_argument("--file", help="file that contains the LFB data. Default = {})".format(file))
parser.pictures()

## A script may only parse a few of the command-line arguments,
## passing the remaining arguments on to another script or program.
args = parser.parse_known_args()[0]
if args.file:
    file = args.file
if args.pictures:
    pictures = int(args.pictures)



# Decode and multiplexing all components (YUV).
#----------------------------------------------
## Current picture number iteration.
picture_number = 0
while picture_number < pictures:

    ## Current picture number iteration.
    str_picture_number = '%04d' % picture_number

    # Y
    #---
    ## Current picture name iteration.
    picture_filename = file + "_Y_" + str_picture_number

    # Decode a component.
    try:
        check_call("trace ltw -D "
                   + " -i " + picture_filename + ".ltw"
                   + " -o " + picture_filename + ".raw"
                   + " -c " + os.environ["MCTF"] + "/bin/config-hfb.txt"
                   + " -a 0"
                   + " -s 0",
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)

    try:
        check_call("trace cat " + picture_filename + ".raw >> " + file, shell=True)
    except CalledProcessError:
        sys.exit(-1)


    # U
    #---
    picture_filename = file + "_U_" + str_picture_number

    # Decode a component.
    try:
        check_call("trace ltw -D "
                   + " -i " + picture_filename + ".ltw"
                   + " -o " + picture_filename + ".raw"
                   + " -c " + os.environ["MCTF"] + "/bin/config-hfb.txt"
                   + " -a 0"
                   + " -s 0",
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)

    try:
        check_call("trace cat " + picture_filename + ".raw >> " + file, shell=True)
    except CalledProcessError:
        sys.exit(-1)

    # V
    #---
    picture_filename = file + "_V_" + str_picture_number

    # Decode a component.
    try:
        check_call("trace ltw -D "
                   + " -i " + picture_filename + ".ltw"
                   + " -o " + picture_filename + ".raw"
                   + " -c " + os.environ["MCTF"] + "/bin/config-hfb.txt"
                   + " -a 0"
                   + " -s 0",
                   shell=True)
    except CalledProcessError:
        sys.exit(-1)

    try:
        check_call("trace cat " + picture_filename + ".raw >> " + file, shell=True)
    except CalledProcessError:
        sys.exit(-1)

    picture_number += 1
