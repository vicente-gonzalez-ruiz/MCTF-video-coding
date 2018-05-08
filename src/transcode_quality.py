#!/usr/bin/env python3
#!/home/vruiz/.pyenv/shims/python -i
# -*- coding: iso-8859-15 -*-

# Transcode a MCTF sequence in quality.
#
# Input:
#
#  Original MJ2K texture sequence and its description (number of
#  GOPs and number of TRLs) and number of quality layers. Motion and
#  type files must be copied.
#
# Output:
# 
#  transcoded MJ2K texture sequence.
#
# Examples:
#
#  mctf transcode_quality --layers=16
#
# Procedure.
#
#  Each temporal subband has been compressed using the same
#  slopes. The slopes has been selected equidistant, and threfore,
#  each subband-layer will contribute with the same quality Q to the
#  corresponding temporal subband. This value depends on the distance
#  between the slopes.
#
#  On the other hand, each temporal subband contributes with a
#  different of energy (~quality) to the reconstruction of the
#  GOP. For example, if L1 is 1.25 times more energetic than H1, each
#  subband-layer of L1 also will contribute 1.25 times more than any
#  other layer of H1. In fact, any subband-layer of L1 contributes
#  1.25*Q where any subband-layer of H1 contributes Q.
#
#  The size of each subband-layer in each subband has a different
#  length. If R is the length of L1.l3 and H1.l3 (supposing 4
#  subband-layers), \sqrt(2)*R will be the length (on average) of
#  L1.l2 and H1.l2. To find an optimal ordering of subband layers in
#  this example, the lengths of the subband-layers of L1 can be
#  considered 1.25 times smaller than the lengths of the
#  subband-layers of H1. So, the slopes generated by the
#  subband-layers of L1 will have 1.25 times the slopes of the
#  subband-layers of H1.
#
#  If the slope (when reconstructing the GOP) of L1.l3 is X, the slope
#  of L1.l2 is X/sqrt(2), the slope of L1.l1 is X/(sqrt(2)^2) and so
#  on. The slope (when reconstructing the GOP) of H1.l3 is X/1.25, the
#  slope of H1.l2 is (X/1.25)/sqrt(2), the slope of H1.l1 is
#  (X/1.25)/(sqrt(2)^2), etc. Therefore, depending on X, each
#  subband-layer of each temporal subband will generate a slope. The
#  optimal subband-layers ordering can be determined by sorting the
#  slopes. For example, is X=5dB, slope(L1.l3)=5,
#  slope(L1.l2)=5/sqrt(2)=3.53. slope(L1.l1)=5/(sqrt(2)^2)=2.5,
#  slope(L1.l0)=5/(sqrt(2)^3)=1.77, slope(H1.l3)=5/1.25=4,
#  slope(H1.l2)=5/1.25/sqrt(2)=2.83, slope(H1.l1)=5/1.25/(sqrt(2)^2)=2
#  and slope(H1.l0)=5/1.25/(sqrt(2)^3)=1.41 The optimal ordering is:
#  L1.l3 (5), H1.l3 (4), L1.l2 (3.53), H1.l2 (2.83), L1.l1 (2.5),
#  H1.l1 (2), L1.l0 (1.77), H1.l0 (1.41).
#
#  If X=1dB, slope(L1.l3)=1 (5 times smaller than in the previous
#  example), slope(H1.l3)=1/1.25=0.8, slope(L1.l2)=1/sqrt(2)=0.71,
#  slope(H1.l2)=1/1.25/sqrt(2)=0.56, slope(L1.l1)=1/sqrt(2)^2=0.5,
#  slope(H1.l1)=1/1.25/sqrt(2)^2=0.4, slope(L1.l0)=1/sqrt(2)^3=0.35,
#  slope(H1.l0)=1/1.25/sqrt(2)^3=0.28. Logically, the ordering does
#  not varie as a function of Q.
#
#  If we use for example 8 quality layers, slope(L1.l7)=1,
#  slope(L1.l6)=1/sqrt(2), slope(L1.l5)=1/sqrt(2)=^2 ... and
#  slope(H1.l7)=1/1.25, slope(H1.l6)=1/1.25/sqrt(2) ..., so the
#  ordering is the same than in the previous example.
#
#  If TRLs=3, we have the following subband attenuations: 1.0,
#  1.2500103877, 1.8652117304. For 4 quality-layers, we have:
# 
#  slope(L2.l3)=1,
#  slope(L2.l2)=1/sqrt(2)=0.71,
#  slope(L2.l1)=1/sqrt(2)^2=0.5,
#  slope(L2.l0)=1/sqrt(2)^3=0.35,
#  slope(H2.l3)=1/1.25=0.8,
#  slope(H2.l2)=1/1.25/sqrt(2)=0.56,
#  slope(H2.l1)=1/1.25/sqrt(2)^2=0.4,
#  slope(H2.l0)=1/1.25/sqrt(2)^3=0.28,
#  slope(H1.l3)=1/1.86=0.54,
#  slope(H1.l2)=1/1.86/sqrt(2)=0.38,
#  slope(H1.l1)=1/1.86/sqrt(2)^2=0.26,
#  slope(H1.l0)=1/1.86/sqrt(2)^3=0.19.
# 
#  So the ordering is:
#
#   1. L2.l3 (1),
#   2. H2.l3 (0.8),
#   3. L2.l2 (0.71),
#   4. H2.l2 (0.56),
#   5. H1.l3 (0.54),
#   6. L2.l1 (0.5),
#   7. H2.l1 (0.4),
#   8. H1.l2 (0.38),
#   9. L2.l0 (0.35),
#  10. H2.l0 (0.28),
#  11. H1.l1 (0.26),
#  12. H1.l0 (0.19)

# {{{ Importing

import logging
import sys
from   GOP              import GOP
from   subprocess       import check_call
from   subprocess       import CalledProcessError
from   arguments_parser import arguments_parser
import io
import operator
import math

# }}}

# {{{ Logging

logging.basicConfig()
log = logging.getLogger("transcode_quality")
log.setLevel('INFO')

# }}}

# {{{ Arguments parsing

parser = arguments_parser(description="Transcodes in quality a MCJ2K sequence.")
parser.GOPs()
parser.add_argument("--keep_layers",
                    help="Number of quality layers to output",
                    default=16)
parser.TRLs()
parser.layers()

args = parser.parse_known_args()[0]
GOPs = int(args.GOPs)
keep_layers = int(args.keep_layers)
TRLs = int(args.TRLs)
layers = int(args.layers)

log.info("GOPs = {}".format(GOPs))
log.info("keep_layers = {}".format(keep_layers))
log.info("TRLs = {}".format(TRLs))
log.info("layers = {}".format(layers))

# }}}

# {{{ Set attenuations among temporal subbands

if   TRLs == 1 :
    pass
elif TRLs == 2 :
    gain = [1.0, 1.2460784922] # [L1/H1]
elif TRLs == 3 :
    gain = [1.0, 1.2500103877, 1.8652117304] # [L2/H2, L2/H1]
elif TRLs == 4 :
    gain = [1.0, 1.1598810146, 2.1224082769, 3.1669663339]
elif TRLs == 5 :
    gain = [1.0, 1.0877939347, 2.1250255455, 3.8884779989, 5.8022196044]
elif TRLs == 6 :
    gain = [1.0, 1.0456562538, 2.0788785438, 4.0611276369, 7.4312544148, 11.0885981772]
elif TRLs == 7 :
    gain = [1.0, 1.0232370223, 2.0434169985, 4.0625355976, 7.9362383342, 14.5221257323, 21.6692913386]
elif TRLs == 8 :
    gain = [1.0, 1.0117165706, 2.0226778348, 4.0393126714, 8.0305936232, 15.6879129862, 28.7065276104, 42.8346456693]
else :
    sys.stderr.write("Gains are not available for " + str(TRLs) + " TRLs. Enter them in transcode_quality.py")
    exit (0)

# }}}

# {{{ GOPs and images

gop=GOP()
GOP_size = gop.get_size(TRLs)
log.info("GOP_size = {}".format(GOP_size))

images = (GOPs - 1) * GOP_size + 1
log.info("images = {}".format(images))

# }}}

# {{{ Compute slope averages

# H subbands
subband = 1
while subband < TRLs:
    images = (images + 1) // 2
    average = [0]*layers

    for image in range(images-1):    
        fname = "high_{}_{:04d}_Y.txt".format(subband, image)
        with io.open(fname, 'r') as file:
            slopes = file.read().replace(' ','').replace('\n','').split(',')
        log.info("{}: {}".format(fname, slopes))
        for i in range(layers):
            average[i] += int(slopes[i])

    for l in range(layers):
        average[l] //= (images-1)

    log.info("high_{}: {}".format(subband, average))

    with io.open("high_{}.txt".format(subband), 'w') as file:
        for i in average:           
            file.write("{} ".format(i))

    subband += 1
    
# L subband
average = [0]*layers
for image in range(GOPs):
    fname = "low_{}_{:04d}_Y.txt".format(TRLs-1, image)
    with io.open(fname, 'r') as file:
        slopes = file.read().replace(' ','').replace('\n','').split(',')
    log.info("{}: {}".format(fname, slopes))        
    for i in range(layers):
        average[i] += int(slopes[i])

for l in range(layers):
    average[l] //= GOPs

log.info("low_{}: {}".format(subband, average))
    
with io.open("low_{}.txt".format(TRLs-1), 'w') as file:
    for i in average:
        file.write("{} ".format(i))

# }}}

#import pdb; pdb.set_trace()
# {{{ Define subband_layers: a list of tuples ('L'|'H', subband, layer, slope)

subband_layers = []
    
# L
with io.open("low_{}.txt".format(TRLs-1), 'r') as file:
    slopes = file.read().split()
range_of_slopes = int(slopes[0]) - int(slopes[layers-1])
for index, slope in enumerate(slopes):
    subband_layers.append(('L', TRLs-1, layers-index-1, int(slope)-42000))

# H's
for subband in range(1,TRLs):
    with io.open("high_{}.txt".format(subband)) as file:
        slopes = file.read().split()
    for index, slope in enumerate(slopes):
        #subband_layers.append(('H', TRLs-subband, layers-index-1, int(float(slope)//gain[subband])))
        #subband_layers.append(('H', TRLs-subband, layers-index-1, int(slope)))
        #subband_layers.append(('H', TRLs-subband, layers-index-1, int(float(slope)-range_of_slopes*gain[subband])))
        subband_layers.append(('H', TRLs-subband, layers-index-1, (int(slope)-42000)//gain[subband]))

log.info("subband_layers={}".format(subband_layers))
        
# }}}

# {{{ Sort and truncate the list of subband-layers

# Sort the subband-layers by their relative slope
subband_layers.sort(key=operator.itemgetter(3), reverse=True)
log.info("(after sorting) subband_layers={}".format(subband_layers))

# Truncate the list
del subband_layers[keep_layers:]
log.info("(after truncating) subband_layers={}".format(subband_layers))

# }}}

# {{{ Count the number of subband-layers per subband

slayers_per_subband = {}
slayers_per_subband[('L', TRLs-1)] = 0
for i in range(TRLs-1,0,-1):
    slayers_per_subband[('H', i)] = 0

for i in subband_layers:
    slayers_per_subband[(i[0], i[1])] += 1

with io.open("layers.txt", 'w') as file:
    log.info("{}:{}".format(('L', TRLs-1), slayers_per_subband[('L', TRLs-1)]))
    file.write("{}:{} ".format(('L', TRLs-1), slayers_per_subband[('L', TRLs-1)]))
    for i in range(TRLs-1,0,-1):
        log.info("{}:{}".format(('H', i), slayers_per_subband[('H', i)]))
        file.write("{}:{} ".format(('H', i), slayers_per_subband[('H', i)]))
    file.write("\n")

# }}}

# {{{ Transcoding

LOW = "low"
HIGH = "high"

# Transcoding of H subbands
subband = 1
while subband < TRLs:

    images = (images + 1) // 2
    if slayers_per_subband[('H', subband)] > 0:
        log.info("Transcoding subband H[{}] with {} images".format(subband, images - 1))

        try:
            check_call("mctf transcode_quality_subband"
                       + " --subband " + HIGH + "_" + str(subband)
                       + " --layers " + str(slayers_per_subband[('H', subband)])
                       + " --images " + str(images - 1),
                       shell=True)
        except CalledProcessError:
            sys.exit(-1)

        try:
            check_call("trace cp motion_residue_" + str(subband) + "*.j2c transcode_quality",
	               shell=True)
        except CalledProcessError:
            sys.exit(-1)

    subband += 1

# Transcoding of L subband
log.info("Transcoding subband L[{}] with {} images".format(subband, images - 1))
try:
    check_call("mctf transcode_quality_subband"
               + " --subband " + LOW + "_" + str(TRLs - 1)
               + " --layers " + str(slayers_per_subband[('L', TRLs - 1)])
               + " --images " + str(GOPs),
               shell=True)
except CalledProcessError:
    sys.exit(-1)

# }}}
