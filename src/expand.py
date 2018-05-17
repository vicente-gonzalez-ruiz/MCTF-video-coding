#!/usr/bin/env python3
# -*- coding: iso-8859-15 -*-

## Decodes a sequence of pictures.
#  Decoding consists of two major steps:
#  - Decompression textures and movement data.
#  - Synthesizes the video.
#
#  Examples:
#  - Show default parameters.
#  mcj2k expand --help
#
#  - Expands using the default parameters.\n
#  mcj2k expand
#
#  - Example of use.
#  expand --update_factor=0 --GOPs=1 --TRLs=5 --SRLs=5 --block_size=32
#    --min_block_size=32 --search_range=4 --pixels_in_x=352
#    --pixels_in_y=288 --subpixel_accuracy=0

import sys
from GOP import GOP
from shell import Shell as shell
from arguments_parser import arguments_parser
from colorlog import log

parser = arguments_parser(description="Decodes a MCJ2K stream into a sequence of pictures.")
parser.block_size()
parser.block_overlaping()
parser.border_size()
parser.GOPs()
parser.min_block_size()
parser.pixels_in_x()
parser.pixels_in_y()
parser.search_range()
parser.SRLs()
#parser.add_argument("--subband_layers",
#                    help="Number of subband-layers to decode",
#                    default=1)
parser.subpixel_accuracy()
parser.TRLs()
parser.update_factor()

args = parser.parse_known_args()[0]

block_overlaping = int(args.block_overlaping)
log.info("block_overlaping={}".format(block_overlaping))

block_size = str(args.block_size)
log.info("block_size={}".format(block_size))

border_size = int(args.border_size)
log.info("border_size={}".format(border_size))

GOPs = int(args.GOPs)
log.info("GOPs={}".format(GOPs))

min_block_size = int(args.min_block_size)
log.info("min_block_size={}".format(min_block_size));

pixels_in_x = str(args.pixels_in_x)
log.info("pixels_in_x={}".format(pixels_in_x))

pixels_in_y = str(args.pixels_in_y)
log.info("pixels_in_y={}".format(pixels_in_y))

search_range = int(args.search_range)
log.info("search_range={}".format(search_range))

SRLs = int(args.SRLs)
log.info("TRLs={}".format(TRLs))

subpixel_accuracy = str(args.subpixel_accuracy)
log.info("subpixel_accuracy={}".format(subpixel_accuracy))

TRLs = int(args.TRLs)
log.info("TRLs={}".format(TRLs))

#subband_layers = int(args.subband_layers)
update_factor = float(args.update_factor)
log.info("update_fact={}".format(update_factor))

# Time
# /usr/bin/time -f "# Real-User-System\n%e\t%U\t%S" -a -o "info_time" date
# /usr/bin/time -f "%e\t%U\t%S" -a -o "info_time_" date

#for sl in range(subband_layers):
#    try:
#        check_call("mctf texture_subband_layer_expand"

# Decompress texture.
shell.run("mctf texture_expand"
          + " --GOPs=" + str(GOPs)
          + " --pixels_in_x=" + str(pixels_in_x)
          + " --pixels_in_y=" + str(pixels_in_y)
          + " --SRLs=" + str(SRLs)
          + " --TRLs=" + str(TRLs))

## Decompress motion data.
if TRLs > 1:
    shell.run("mctf motion_expand"
              + " --block_size="  + str(block_size)
              + " --GOPs=" + str(GOPs)
              + " --pixels_in_x=" + str(pixels_in_x)
              + " --pixels_in_y=" + str(pixels_in_y)
              + " --TRLs=" + str(TRLs))

    shell.run("mctf synthesize"
              + " --GOPs=" + str(GOPs)
              + " --TRLs=" + str(TRLs)
              + " --block_size=" + str(block_size)
              + " --pixels_in_x=" + str(pixels_in_x)
              + " --pixels_in_y=" + str(pixels_in_y)
              + " --subpixel_accuracy=" + str(subpixel_accuracy)
              + " --search_range=" + str(search_range)
              + " --block_overlaping=" + str(block_overlaping)
              + " --update_factor=" + str(update_factor))
