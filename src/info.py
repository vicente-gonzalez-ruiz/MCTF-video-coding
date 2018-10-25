#!/bin/sh
''''exec python3 -O -- "$0" ${1+"$@"} # '''
#!/usr/bin/env python3
# -*- coding: iso-8859-15 -*-

# Show data-rate information of the MCTF structure:
#
# 0 1 2 3 4 5 6 7 8
# 0               8 L_3
#         4         H_3
#     2       6     H_2
#   1   3   5   7   H_1

import sys
import io
from GOP import GOP
from arguments_parser import arguments_parser
import os
from colorlog import ColorLog
import logging

log = ColorLog(logging.getLogger("info"))
log.setLevel('INFO')

parser = arguments_parser(description="Show information.")
parser.add_argument("--FPS",
                    help="Frames Per Second",
                    default=30)
parser.GOPs()
parser.TRLs()

args = parser.parse_known_args()[0]
FPS = float(args.FPS)
GOPs = int(args.GOPs)
TRLs = int(args.TRLs)

gop = GOP()
GOP_size = gop.get_size(TRLs)
pictures = GOP_size*(GOPs-1)+1
# Weighting value, to be applied between the GOP0, and the rest.
average_ponderation = (pictures-1.0)/pictures
GOP0_time = 1.0/FPS
GOP_time = float(GOP_size)/FPS

IMG_EXT = os.environ["MCTF_IMG_EXT"]

sys.stdout.write("\n" + sys.argv[0] + ":\n\n")
sys.stdout.write("TRLs           = " + str(TRLs) + " temporal resolution levels\n")
sys.stdout.write("Pictures       = " + str(pictures) + " pictures\n")
sys.stdout.write("FPS            = " + str(FPS) + " frames/second\n")
sys.stdout.write("GOP size       = " + str(GOP_size) + " pictures\n")
sys.stdout.write("Number of GOPs = " + str(GOPs) + " groups of pictures\n")
sys.stdout.write("Frame time     = " + str(GOP0_time) + " seconds\n")
sys.stdout.write("GOP time       = " + str(GOP_time) + " seconds\n")
sys.stdout.write("Total time     = " + str(pictures/FPS) + " seconds\n")
sys.stdout.write("\nAll the values are given in thousands (1000) of bits per second (Kbps).\n")

# Table header.

# First line. (TRL4 TRL3 TRL2 TRL1 TRL0).
sys.stdout.write("\n     ")
sys.stdout.write(" TRL" + str(TRLs-1))

for i in range(TRLs-1, 0, -1):
    sys.stdout.write("        ")
    sys.stdout.write("TRL" + str(i-1))
#sys.stdout.write("    Total    Total\n");
sys.stdout.write("\n")

# Second line. (GOP L_4 R_4+H_4 R_3+H_3 R_2+H_2 R_1+H_1 Total Average).
sys.stdout.write("GOP#")
sys.stdout.write("   L_" + str(TRLs-1))

for i in range(TRLs-1, 0, -1):
    sys.stdout.write("   R_" + str(i) + "   H_" + str(i))
sys.stdout.write("      GOP    Video\n")

# Third line. (--------------------------------------)
sys.stdout.write("---- ")
sys.stdout.write("----- ")
for i in range(TRLs-1, 0, -1):
    sys.stdout.write("----------- ")
sys.stdout.write("-------- --------\n")

# Computations

# {{{ GOP 0. The GOP0 is formed by the first picture in L_<TRLs-1>.

length_0 = 0
filename = "L_" + str(TRLs - 1) + "/" + "%04d" % 0 + "." + IMG_EXT
try:
    with io.open(filename, "rb") as file:
        file.seek(0, 2)
        length_0 += file.tell()
except:
    pass

Kbps_total = 0
Kbps_total_pro = 0

kbps = float(length_0) * 8.0 / GOP0_time / 1000.0
sys.stdout.write("0000 %5d" % kbps)
time = GOP0_time

for subband in range(TRLs-1, 0, -1):
    sys.stdout.write(" %5d" % 0)
    sys.stdout.write(" %5d" % 0)

sys.stdout.write(" %8d" % kbps)
sys.stdout.write(" %8d" % kbps)
sys.stdout.write("\n")

# }}}

# {{{ Rest of GOPs

total = 0
for GOP_number in range(1, GOPs):

    length_GOP = 0
    sys.stdout.write("%3s" % '%04d' % (GOP_number))

    # {{{ L
   
    length = 0
    filename = "L_" + str(TRLs - 1) + "/" + "%04d" % GOP_number + "." + IMG_EXT
    try:
        with io.open(filename, "rb") as file:
            file.seek(0, 2)
            length += file.tell()
    except:
        if __debug__:
            log.warning("{} is missing".format(filename))
        else:
            pass

    kbps = float(length) * 8.0 / GOP_time / 1000.0
    sys.stdout.write(" %5d" % int(round(kbps)))
    length_GOP += length

    # }}}
  
    # {{{ Rest of subbands

    pics_in_subband = 1
    for subband in range(TRLs-1, 0, -1):

        #import ipdb; ipdb.set_trace()

        # Motion
        length = 0
        for i in range(pics_in_subband):
            filename = "R_" + str(subband) + "/" + \
                "%04d" % ((GOP_number-1)*(pics_in_subband-1)+i) + ".j2c"
            try:
                with io.open(filename, "rb") as file:
                    file.seek(0, 2)
                    length += file.tell()
            except:
                if __debug__:
                    log.warning("{} is missing".format(filename))
                else:
                    pass

        kbps = float(length) * 8.0 / GOP_time / 1000.0
        sys.stdout.write(" %5d" % int(round(kbps)))
        length_GOP += length

        # Texture
        length = 0
        for i in range(pics_in_subband):
            filename = "H_" + str(subband) + "/" \
                + "%04d" % ((GOP_number-1)*(pics_in_subband-1)+i) + "." + IMG_EXT
            try:
                with io.open(filename, "rb") as file:
                    file.seek(0, 2)
                    length += file.tell()
            except:
                if __debug__:
                    log.warning("{} is missing".format(filename))
                else:
                    pass

        kbps = float(length) * 8.0 / GOP_time / 1000.0
        sys.stdout.write(" %5d" % int(round(kbps)))
        length_GOP += length

        pics_in_subband *= 2

    total += length_GOP

    kbps = float(length_GOP) * 8.0 / GOP_time / 1000.0
    sys.stdout.write(" %8d" % kbps)

    length_total = length_0 + total
    kbps = float(length_total) * 8.0 / (GOP0_time + GOP_time*GOP_number) / 1000.0
    sys.stdout.write(" %8d" % kbps)

    #sys.stdout.write(" %8d" % length_total)
    #sys.stdout.write("%8.3f" % (GOP0_time + GOP_time*GOP_number))
    sys.stdout.write("\n")

sys.stdout.write("\nAverage bit-rate (Kbps) = {}\n".format(kbps))
