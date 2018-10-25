#!/bin/sh
''''exec python3 -- "$0" ${1+"$@"} # '''
#!/usr/bin/env python3
#!/home/vruiz/.pyenv/shims/python -i
# -*- coding: iso-8859-15 -*-

# {{{ Transcode a MCTF sequence in quality.

# Input:
#
#  MJ2K texture sequence.
#
# Output:
#
#  Transcoded MJ2K texture sequence.
#
# Examples:
#
#  mctf transcode_quality --keep_layers=16
#
# Procedure.
#
#  Each temporal subband has been compressed with a number of quality
#  layers. Each quality layer has a slope. This script, GOP by GOP
#  reads the slopes of each quality layer (computing an average if
#  more than one image per temporal subband is found), scales them
#  using the theoretical subband gains which should convert MCTF into
#  a uniform transform, sorts the subbands-layers by their
#  contribution and finally, truncates the Input using this
#  information, to produce the Output.

# }}}

# --------------------------------------------------------------------
#import ipdb; ipdb.set_trace()

# {{{ Importing
import sys
from GOP import GOP
from arguments_parser import arguments_parser
import io
import operator
from shell import Shell as shell
from colorlog import ColorLog
import logging

import os
import math
import subprocess as sub
from subprocess   import check_call
from subprocess   import CalledProcessError

log = ColorLog(logging.getLogger("transcode_quality"))
log.setLevel('DEBUG')
shell.setLogger(log)

# }}}

# {{{ Arguments parsing

parser = arguments_parser(
    description="Transcodes in quality a MCJ2K sequence.")
parser.GOPs()
parser.add_argument("--keep_layers",
                    help="Number of quality layers to output",
                    default=16)
parser.TRLs()
parser.layers()
parser.add_argument("--destination",
                    help="destination directory (must exist)",
                    default="transcode_quality")
parser.slope()
parser.add_argument("--FPS",
                    help="Number of frames per second",
                    default=30)
parser.pixels_in_x()
parser.pixels_in_y()
parser.block_size()
parser.search_range()
parser.add_argument("--video",
                    help="Original video path and name",
                    default="/home/cmaturana/Videos/container_352x288x30x420x300.avi")


args = parser.parse_known_args()[0]

GOPs         = int(args.GOPs)
keep_layers  = int(args.keep_layers)
TRLs         = int(args.TRLs)
layers       = int(args.layers)
destination  = args.destination
slope        = int(args.slope)
FPS          = float(args.FPS)
x_dim        = int(args.pixels_in_x)
y_dim        = int(args.pixels_in_y)
block_size   = int(args.block_size)
search_range = int(args.search_range)
video        = args.video

log.info("GOPs={}".format(GOPs))
log.info("keep_layers={}".format(keep_layers))
log.info("TRLs={}".format(TRLs))
log.info("layers={}".format(layers))
log.info("destination={}".format(destination))
log.info("slope={}".format(slope))
log.info("FPS={}".format(FPS))
log.info("pixels_in_x={}".format(x_dim))
log.info("pixels_in_y={}".format(y_dim))
log.info("block_size={}".format(block_size))
log.info("search_range={}".format(search_range))
log.info("video={}".format(video))
# }}}

destination_zero = "zero_texture"

# --------------------------------------------------------------------
def transcode_picture(filename_in, filename_out, layers):
    # {{{ 
    log.debug("transcode_picture: {} to {}/{} with {} layers, from gop {}".format(filename_in, destination, filename_out, layers, gop+1))
    if layers > 0:
        shell.run("trace kdu_transcode"
                  + " -i " + filename_in
                  + " -jpx_layers sYCC,0,1,2"
                  + " -o " + destination + "/" + filename_out
                  + " Clayers=" + str(layers))
    # }}}

# --------------------------------------------------------------------
def transcode_images(layersub):
    # {{{
    log.debug("transcode_images={}".format(layersub))

    for key, value in layersub.items():
        pics_per_subband = (1 << (TRLs-key[1]-1))
        for p in range(pics_per_subband * gop, pics_per_subband * gop + pics_per_subband):
            if key[0] == 'L':
                fname = "L_" + str(key[1]) + '/' + str('%04d' % (p+1)) + ".jpx"
                transcode_picture(fname, fname, value)

                # {{{ Transcode GOP0, using the same number of subband layers than the last GOP
                if gop == 0:
                    fname  = "L_" + str(key[1]) + '/' + str('%04d' % (p)) + ".jpx"
                    value  = layersub[("L", TRLs-1)]
                    transcode_picture(fname, fname, value)
                # }}}

            elif key[0] == 'H':
                fname = "H_" + str(key[1]) + '/' + str('%04d' % p) + ".jpx"
                transcode_picture(fname, fname, value)

            elif key[0] == 'R':
                if value > 0:
                    fname = "R_" + str(key[1]) + '/' + str('%04d' % p) + ".j2c"
                    shell.run("trace cp " + fname + ' ' + destination + '/' + fname)
    # }}}

# --------------------------------------------------------------------
def transcode_images_singleGOP(layersub):
    # {{{
    log.debug("transcode_images_singleGOP={}".format(layersub))

    for key, value in layersub.items():
        pics_per_subband = (1 << (TRLs-key[1]-1))

        log.info("key={}".format(key))
        log.info("pics_per_subband={}".format(pics_per_subband))

        for p in range(pics_per_subband * gop, pics_per_subband * gop + pics_per_subband):
            if key[0] == 'L':
                fname_in  = "L_" + str(key[1]) + '/' + str('%04d' % (p+1)) + ".jpx"
                fname_out = "L_" + str(key[1]) + '/' + str('%04d' % (p-(pics_per_subband * gop)+1)) + ".jpx"
                transcode_picture(fname_in, fname_out, value)
                
                # {{{ Transcode GOP0, using the same number of subband layers than the last GOP
                fname_in  = "L_" + str(key[1]) + '/' + str('%04d' % (p)) + ".jpx"
                fname_out = "L_" + str(key[1]) + '/' + str('%04d' % (p-(pics_per_subband * gop))) + ".jpx"
                value     = layersub[("L", TRLs-1)]
                transcode_picture(fname_in, fname_out, value)
                # }}}

            elif key[0] == 'H':
                fname_in  = "H_" + str(key[1]) + '/' + str('%04d' % p) + ".jpx"
                fname_out = "H_" + str(key[1]) + '/' + str('%04d' % (p-(pics_per_subband * gop))) + ".jpx"
                transcode_picture(fname_in, fname_out, value)

            elif key[0] == 'R':
                if value > 0:
                    fname_in  = "R_" + str(key[1]) + '/' + str('%04d' % p) + ".j2c"
                    fname_out = "R_" + str(key[1]) + '/' + str('%04d' % (p-(pics_per_subband * gop))) + ".j2c"
                    shell.run("trace cp " + fname_in + ' ' + destination + '/' + fname_out)
    # }}}

# --------------------------------------------------------------------
def raw_pgm(GOPs_to_extract):

    raw_pgm = pwd + "/../raw_pgm.sh"
    param   = " -g " + str(GOPs_to_extract) + " -t " + str(TRLs) + " -y " + str(y_dim) + " -x " + str(x_dim)
    shell.run(raw_pgm + param)

    #if True == os.path.isfile(raw_pgm):
    #    shell.run(raw_pgm + param)


# --------------------------------------------------------------------
def codestream_point(path, GOPs_to_extract, original): # A single gop or whole video

    os.chdir(path)
    
    # Create zero texture
    shell.run("mctf create_zero_texture --pixels_in_y=" + str(y_dim) + " --pixels_in_x=" + str(x_dim))

    # KBPS
    # ------------------------
    
    # Info without previous gop
    if GOPs_to_extract < GOPs and True == os.path.isfile("L_" + str(TRLs-1) + "/0000.jpx"):
        shell.run("mkdir previous_gop; mv L_" + str(TRLs-1) + "/0000.jpx previous_gop")

    # INFO
    p = sub.Popen("mctf info --GOPs=" + str(GOPs_to_extract) + " --TRLs=" + str(TRLs) + " --FPS=" + str(FPS) + " 2> /dev/null | grep \"Average\" | cut -d \" \" -f 5", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    out, err = p.communicate()
    kbps = float(out)
    
    # Info without previous gop
    if True == os.path.isdir("previous_gop"):
        shell.run("mv previous_gop/* " + "L_" + str(TRLs-1) + "; rm -rf previous_gop")
    
    # Expand
    # ------------------------
    shell.run("mctf expand --GOPs=" + str(GOPs_to_extract) + " --TRLs=" + str(TRLs) + " --block_size=" + str(block_size) + " --search_range=" + str(search_range) + " --pixels_in_y=" + str(y_dim) + " --pixels_in_x=" + str(x_dim))
    # Separate to images
    raw_pgm(GOPs_to_extract)

    # PSNR
    # ------------------------
    p = sub.Popen("mctf psnr --file_A L_0 --file_B " + original + " --pixels_in_x=" + str(x_dim) + " --pixels_in_y=" + str(y_dim) + " --GOPs=" + str(GOPs_to_extract) + " --TRLs=" + str(TRLs)
                , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
    out, err = p.communicate()
    log.debug("psnr: " + str(out))
    psnr = float(out.decode('ascii'))

    return kbps, psnr

# --------------------------------------------------------------------
def add_layer():

    if (key[0] == 'R' and try_layersub[key] < 1) or ((key[0] == 'L' or key[0] == 'H') and try_layersub[key] < layers):
        try_layersub[key] += 1
        return 0
    else:
        return 1

# --------------------------------------------------------------------
def trace_selection(mode):
    if mode == -2:
        shell.run("echo \"\" > " + str(pwd) + "/selection.dat")
    elif mode == -1:
        shell.run("echo \"--- EMPTY LAYER ---\" >> " + str(pwd) + "/selection.dat")
    elif mode == 0:
        shell.run("echo \"\nGOP " + str(gop+1) + " from 0 to " + str(GOPs-1) + " GOPs\n\" >> " + str(pwd) + "/selection.dat")
        shell.run("echo \"Angle = math.atan((psnr - old_psnr) / (kbps - old_kbps))\n\" >> " + str(pwd) + "/selection.dat")
    elif mode == 1:
        shell.run("echo \"" + str(key) + ": " + str(try_layersub[key]) + "\t\t" + str("%.8f"%angle) + "\t= " + "(" + str("%.6f"%psnr) + " - " + str("%.6f"%old_psnr) + ") / (" + str("%.4f"%kbps) + " (+" + str("%.1f"%kbps_zero) + ") - " + str("%.4f"%old_kbps) + ")\" >> " + str(pwd) + "/selection.dat")
    elif mode == 2:
        shell.run("echo \"ADDED: " + str(point["subband"]) + ": " + str(point["layer"]) + "  THEN: " + str(best_layersub) + "\n\" >> " + str(pwd) + "/selection.dat")
    elif mode == 3:
        shell.run("echo \"" + str(FSO[gop][point]) + "\" >> " + str(pwd) + "/selection_curveFSO.dat")
    elif mode == 4:
        if False == os.path.isfile(file_results + "_curveFSO.dat"):
            shell.run("echo \"" + "#KBPS #PSNR #KBPS_HEADERS" + "\" >> " + file_results + "_curveFSO.dat")
        shell.run("echo \"" + str("%.6f"%float(kbps)) + "\t" + str("%.6f"%float(psnr)) + "\t" + str("%.3f"%float(kbps_zero)) + "\" >> " + file_results + "_curveFSO.dat")
    elif mode == 5:
        shell.run("echo \"\" >> " + str(pwd) + "/selection_curveFSO.dat")

# --------------------------------------------------------------------
def toFile():
    # {{{ Save to file
    shell.run("echo \"# KBPS #PSNR\" >> " + str(pwd) + "/curve_gop" + str(gop+1) + ".dat")
    for z in range(0, len(FSO[gop])):
        shell.run("echo \"" + str(FSO[gop][z]) + "\" >> " + str(pwd) + "/selection_gop" + str(gop+1) + ".dat")
        if z % 2 == 0:
            shell.run("echo \"" + str("%.3f"%float(FSO[gop][z]["kbps"])) + "\t" + str("%.3f"%float(FSO[gop][z]["psnr"])) + "\" >> " + str(pwd) + "/curve_gop" + str(gop+1) + ".dat")
    # }}}

# --------------------------------------------------------------------
def toDirectory():
    # {{{ Save to directory
    f = str(pwd) + "/../FSO_" + str(video.split("/")[len(video.split("/"))-1]) + "_L" + str(layers) + "_T" + str(TRLs) + "_BS" + str(block_size) + "_SR" + str(search_range) +"_G" + str(GOPs) + "_" + str(slope) + ".dat"
    shell.run("rm -rf " + f + "; mkdir " + f)
    shell.run("cp " + str(pwd) + "/*.dat " + f)
    # }}}
    
# --------------------------------------------------------------------
def updatePoint():

    point["kbps"]    = kbps
    point["psnr"]    = psnr
    point["subband"] = key
    point["layer"]   = best_layersub[key]
    point["angle"]   = angle
    return point

# --------------------------------------------------------------------
def init_layersub(mode):

    layersub = {}

    if mode == "empty":
        layersub[('L', TRLs-1)] = 0
        for i in range(TRLs-1,0,-1):
            layersub[('H', i)] = 0
            layersub[('R', i)] = 0

    elif mode == "full":
        layersub[('L', TRLs-1)] = layers
        for i in range(TRLs-1,0,-1):
            layersub[('H', i)] = layers
            layersub[('R', i)] = 1

    return layersub

# --------------------------------------------------------------------
def gop_video():
    # {{{ Take original frames from a gop to compute distortion gop by gop.

    # GOP_0 are: 0001
    # GOP_1 are: 0002 a 0017. Need to expand: 0001 a 00017
    # GOP_2 are: 0018 a 0033. Need to expand: 0017 a 00033

    original_gop_anterior = pwd + "/original_gop" + str(gop)
    original_gop          = pwd + "/original_gop" + str(gop+1)

    shell.run("mkdir " + original_gop)
    for p in range(GOP_size * gop, GOP_size * gop + GOP_size + 1):

        fname_in  = pwd + "/L_0/"      + str('%04d' % (p+1))
        fname_out = original_gop + "/" + str('%04d' % (p-(GOP_size * gop)+1))

        shell.run("cp " + fname_in + ".Y " + fname_out + ".Y")
        shell.run("cp " + fname_in + ".U " + fname_out + ".U")
        shell.run("cp " + fname_in + ".V " + fname_out + ".V")

    #shell.run("rm -f " + original_gop_anterior) # Elimina gops originales.
    return original_gop
    # }}}

# --------------------------------------------------------------------
def if_empty_layer(kbps):
    if kbps == old_kbps:
        kbps += 0.001
        trace_selection(-1)
    return kbps

# --------------------------------------------------------------------
def clean_transcode(path, destination):

    os.chdir(path)
    # {{{ Clean the previus transcode and create directories
    shell.run("rm -rf " + destination + "; mkdir " + destination)
    shell.run("mkdir " + destination + "/L_" + str(TRLs-1))
    for subband in range(TRLs-1, 0, -1):
        shell.run("mkdir " + destination + "/R_" + str(subband))
        shell.run("mkdir " + destination + "/H_" + str(subband))
    # }}}

# --------------------------------------------------------------------
def random_kbps_psnr(): # Only for debug
    import random
    kbps = random.randint(1,101)
    psnr = random.randint(1,101)
    return kbps, psnr

# -------------------------------------------------------------------- MAIN
# --------------------------------------------------------------------
if TRLs == 1:
    log.info("No sense TRL = 1 in FSO.")
    sys.exit(0)

# --------------------------------------------------------------------
# {{{ Compute GOPs and pictures
gop = GOP()
GOP_size = gop.get_size(TRLs)
log.info("GOP_size={}".format(GOP_size))

pictures = GOPs * GOP_size + 1 #  = (GOPs-1) * GOP_size + 1
log.info("pictures={}".format(pictures))

bs = int(x_dim * y_dim * 1.5)
# }}}


# --------------------------------------------------------------------
#               ¡HERE!
# ~/*.avi		/tmp				/transcode_quality
# ~/compresión	/extracción_total	/extracción_parcial
p = sub.Popen("echo $PWD", shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
out, err = p.communicate()
pwd = out.decode('ascii')
pwd = pwd[:len(pwd)-1]

file_results = str(pwd) + "/" + "L" + str(layers) + "_T" + str(TRLs) + "_BS" + str(block_size) + "_SR" + str(search_range) +"_G" + str(GOPs) + "_" + str(slope)

# --------------------------------------------------------------------
# {{{ START FSO
point   = {}
FSO     = [ [] for i in range(GOPs-1) ]
total   = TRLs*2-1

trace_selection(-2)
for gop in range(0, GOPs-1):
    log.info("GOP={}/{}".format(gop, GOPs))

    # The gop of the original video
    original_gop = gop_video()

    # Reset per gop
    layersub = init_layersub("empty") # "empty" / "full"
    trace_selection(0)

    # 0 layers for old values.
    clean_transcode(pwd, destination)
    transcode_images_singleGOP(layersub)
    old_kbps, old_psnr = codestream_point(pwd + "/" + destination, 2, original_gop)

    full = 0
    while full < total:

        point["angle"] = -99
        full = 0
        for key, value in layersub.items():
            try_layersub = layersub.copy()

            # Add one layer to codestream
            out = add_layer()
            if out == 1:
                full += 1
                continue

            clean_transcode(pwd                         , destination)
            clean_transcode(pwd + "/" + destination_zero, destination)

            # Transcode: gop from original video
            os.chdir(pwd)
            transcode_images_singleGOP(try_layersub)
            # Transcode: gop from zero video. To kbps headers calculation.
            os.chdir(pwd + "/" + destination_zero)
            transcode_images_singleGOP(try_layersub)

            # Kbps & Psnr --> # kbps, psnr = random_kbps_psnr() # Only for fast debug
            kbps, psnr           = codestream_point(pwd + "/" + destination                         , 2, original_gop) # Real kbps & psnr calculation from a single gop
            kbps_zero, psnr_zero = codestream_point(pwd + "/" + destination_zero + "/" + destination, 2, pwd + "/" + destination_zero + "/L_0")
            kbps = kbps - kbps_zero

            # Easy solution for posible empty layer
            kbps = if_empty_layer(kbps)
            # Angle = Tan (difference psnr / difference kbps)
            angle = math.atan ( (psnr - old_psnr) / (kbps - old_kbps) )
            trace_selection(1)
            
            # Save the best codestream during the search
            if point["angle"] < angle:
                best_layersub = try_layersub.copy()
                point         = updatePoint()

        if full < total:
            trace_selection(2)

            # New param for next iteration
            layersub = best_layersub.copy()
            old_psnr = point["psnr"]
            old_kbps = point["kbps"]
            FSO[gop].append(point.copy())
            FSO[gop].append(best_layersub.copy())

    toFile()  # Save FSO selections to files

# END FSO.


# --------------------------------------------------------------------
# Transcode, Kbps & Psnr per WHOLE video (no per gop) for FSO short
for point in range(1, len(FSO[0]), 2):
    clean_transcode(pwd, destination)
    clean_transcode(pwd + "/" + destination_zero, destination)
    for gop in range(0, GOPs-1):
        # Transcode: codestream from original video.
        os.chdir(pwd)
        transcode_images(FSO[gop][point])
        # Transcode: codestream from zero texture video. To kbps headers calculation.
        os.chdir(pwd + "/" + destination_zero)
        transcode_images(FSO[gop][point])
        # Trace
        trace_selection(3)

    # Kbps & Psnr
    kbps     , psnr      = codestream_point(pwd + "/" + destination                         , GOPs, pwd + "/L_0")
    kbps_zero, psnr_zero = codestream_point(pwd + "/" + destination_zero + "/" + destination, GOPs, pwd + "/" + destination_zero + "/L_0")
    kbps = kbps - kbps_zero

    # Save point to file
    trace_selection(4)
    trace_selection(5)

toDirectory()   # Save FSO files to directory

sys.exit(0)




# NOTAS ........................................................................
# shell.run("(mplayer /tmp/out.yuv -demuxer rawvideo -rawvideo w=" + str(x_dim) + ":h=" + str(y_dim) + " -loop 0 -fps " + str(FPS) + ") > /dev/null 2> /dev/null")
# (mplayer container_352x288x30x420x300.avi.yuv -demuxer rawvideo -rawvideo w=352:h=288 -loop 0 -fps 30) > /dev/null 2> /dev/null
# wait = input("PRESS ENTER TO CONTINUE.")
# shell.run("mctf copy --GOPs=2 --TRLs=4 --destination=tmp/transcode_quality")

# yuv to avi:   x264 --input-res 352x288 --qp 0 -o video.yuv.avi video.yuv
# avi to yuv:   ffmpeg -i video.yuv.avi video.yuv

# -vcodec rawvideo -pix_fmt yuv420p 

#    log.info("layersub={}".format(layersub))                   #########
#    wait = input("PRESS ENTER TO CONTINUE.")                   #########


    # Extraction to .yuv
#    shell.run("(ffmpeg -y -s " + str(x_dim) + "x" + str(y_dim) + " -pix_fmt yuv420p -i L_0/%4d.Y " + str(reconstruction) + ".yuv) > /dev/null 2> /dev/null")

    # PSNR
    # ------------------------
    # mctf psnr --file_A L_0 --file_B ../L_0 --pixels_in_x=$x_dim --pixels_in_y=$y_dim --GOPs=$GOPs --TRLs=$TRLs
#    p = sub.Popen("(snr --type=uchar --peak=255"
#                + " --file_A=" + str(original) + ".yuv"
#                + " --file_B=" + str(reconstruction) + ".yuv"
#                + " --block_size=" + str(bs) + ") 2> /dev/null"
#                + " | grep PSNR | grep dB | cut -d \"=\" -f 2"
#                , shell=True, stdout=sub.PIPE, stderr=sub.PIPE)
#    out, err = p.communicate()
#    log.debug("psnr: " + str(out))
#    psnr = float(out.decode('ascii'))



# --------------------------------------------------------------------
#def gop_video():
    # {{{ Take original frames from a gop to compute distortion gop by gop.
#    original_gop_anterior = str(pwd) + "/original_gop" + str(gop)
#    original_gop          = str(pwd) + "/original_gop" + str(gop+1)

#    shell.run("dd"
#            + " if="    + video + ".yuv"
#            + " of="    + str(original_gop) + ".yuv"
#            + " skip="  + str(GOP_size * gop)   # Jump to the current GOP.
#            + " bs="    + str(bs)               # Image size.
#            + " count=" + str(GOP_size + 1))    # images gop + image gop_0.

    #shell.run("rm -f " + original_gop_anterior + ".yuv") # Jse


#    return original_gop
    # }}}
    
    
    
# Kbps & Psnr
# kbps     , psnr      = codestream_point(pwd + "/" + destination                         , GOPs, video, "reconstruction_point" + str(int((point+1)/2)))
# kbps_zero, psnr_zero = codestream_point(pwd + "/" + destination_zero + "/" + destination, GOPs, video, "reconstruction_point" + str(int((point+1)/2)))


# Original .avi to .yuv for cut a gop of the original video
#if False == os.path.isfile(str(video) + ".yuv"):
#    shell.run("ffmpeg -i " + str(video) + " -y " + str(video) + ".yuv")

