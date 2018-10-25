#!/bin/bash

#video=~/Videos/mobile_352x288x30x420x300.avi
video=~/Videos/container_352x288x30x420x300.avi
#video=~/Videos/moving_circle.avi
GOPs=9
TRLs=2
SRLs=5
#GOPs=1
#TRLs=4
y_dim=288
x_dim=352
FPS=30
layers=8  # Be careful, unable to handle more than 10 quality layers
	  # (reason: kdu_compress's output format)
keep_layers=8
#slope=0
slope=43000
#slope=39000
#slope=40000
block_size=16
block_overlaping=0
border_size=0
min_block_size=16
search_range=4
subpixel_accuracy=0

__debug__=1
BPP=8
MCTF_QUANTIZER=automatic

usage() {
    echo $0
    echo "  [-v video file name ($video)]"
    echo "  [-g GOPs ($GOPs)]"
    echo "  [-x X dimension ($x_dim)]"
    echo "  [-y Y dimension ($y_dim)]"
    echo "  [-f frames/second ($FPS)]"
    echo "  [-t TRLs ($TRLs)]"
    echo "  [-l layers ($layers)]"
    echo "  [-k keep layers ($keep_layers)]"
    echo "  [-s slope ($slope)]"
    echo "  [-? (help)]"
}

(echo $0 $@ 1>&2)

while getopts "v:p:x:y:f:t:g:l:k:s:?" opt; do
    case ${opt} in
	v)
	    video="${OPTARG}"
	    echo video=$video
	    ;;
	x)
	    x_dim="${OPTARG}"
	    echo x_dim=$x_dim
	    ;;
	y)
	    y_dim="${OPTARG}"
	    echo y_dim=$y_dim
	    ;;
	f)
	    FPS="${OPTARG}"
	    echo FPS=$FPS
	    ;;
	t)
	    TRLs="${OPTARG}"
	    echo TRLs=$TRLs
	    ;;
	g)
	    GOPs="${OPTARG}"
	    echo GOPs=$GOPs
	    ;;
	l)
	    layers="${OPTARG}"
	    echo layers=$layers
	    ;;
	k)
	    keep_layers="${OPTARG}"
	    echo keep_layers=$keep_layers
	    ;;
	s)
	    slope="${OPTARG}"
	    echo slope=$slope
	    ;;
	?)
            usage
            exit 0
            ;;
        \?)
            echo "Invalid option: -${OPTARG}" >&2
            usage
            exit 1
            ;;
        :)
            echo "Option -${OPTARG} requires an argument." >&2
	    usage
            exit 1
            ;;
    esac
done

if [ $BPP -eq 16 ]; then

    RAWTOPGM () {
	local input_image=$1
	local x_dim=$2
	local y_dim=$3
	local output_image=$4
	(uchar2ushort < $input_image > /tmp/1) 2> /dev/null
	#(add Short 32768 < /tmp/1 > /tmp/2) 2> /dev/null
	rawtopgm -bpp 2 $x_dim $y_dim < /tmp/1 > $output_image
    }

    PGMTORAW () {
	local input_image=$1
	local output_image=$2
	convert -endian MSB $input_image /tmp/1.gray
	#(add Short -32768 < /tmp/1.gray > /tmp/2) 2> /dev/null
	(ushort2uchar < /tmp/1.gray > $output_image) 2> /dev/null
    }
    
else

    RAWTOPGM () {
	local input_image=$1
	local x_dim=$2
	local y_dim=$3
	local output_image=$4
	rawtopgm $x_dim $y_dim < $input_image > $output_image
    }

    PGMTORAW () {
	local input_image=$1
	local output_image=$2
	convert $input_image /tmp/1.gray
	mv /tmp/1.gray $output_image
    }
    
fi

if [ $__debug__ -eq 1 ]; then
    set -x
    set -e
    set -o errexit
fi

rm -rf L_0
mkdir L_0
number_of_images=`echo "2^($TRLs-1)*($GOPs-1)+1" | bc`
if [ $__debug__ -eq 1 ]; then
   ffmpeg -i $video -c:v rawvideo -pix_fmt yuv420p -vframes $number_of_images L_0/%4d.Y 
fi
(ffmpeg -i $video -c:v rawvideo -pix_fmt yuv420p -vframes $number_of_images L_0/%4d.Y) > /dev/null 2> /dev/null
x_dim_2=`echo $x_dim/2 | bc`
y_dim_2=`echo $y_dim/2 | bc`
img=1
while [ $img -le $number_of_images ]; do
    _img=$(printf "%04d" $img)
    #let img_1=img-1
    img_1=$((img-1))
    _img_1=$(printf "%04d" $img_1)
    #(uchar2short < L_0/$_img.Y > /tmp/1) 2> /dev/null
    #rawtopgm -bpp 2   $x_dim   $y_dim < /tmp/1 > L_0/${_img_1}_0.pgm
    input=L_0/$_img.Y
    output=L_0/${_img_1}_0.pgm
    #rawtopgm   $x_dim   $y_dim < $input > $output.pgm
    RAWTOPGM $input $x_dim $y_dim $output

    #(uchar2short < L_0/$_img.U > /tmp/1) 2> /dev/null
    #rawtopgm -bpp 2 $x_dim_2 $y_dim_2 < /tmp/1 > L_0/${_img_1}_1.pgm
    input=L_0/$_img.U
    output=L_0/${_img_1}_1.pgm
    #rawtopgm $x_dim_2 $y_dim_2 < $input > $output.pgm
    RAWTOPGM $input $x_dim_2 $y_dim_2 $output    
    
    #(uchar2short < L_0/$_img.V > /tmp/1) 2> /dev/null
    #rawtopgm -bpp 2 $x_dim_2 $y_dim_2 < /tmp/1 > L_0/${_img_1}_2.pgm
    #rawtopgm $x_dim_2 $y_dim_2 < L_0/$_img.V > L_0/${_img_1}_2.pgm
    input=L_0/$_img.V
    output=L_0/${_img_1}_2.pgm
    RAWTOPGM $input $x_dim_2 $y_dim_2 $output
    #let img=img+1
    img=$((img+1))
done

#mctf create_zero_texture  --pixels_in_y=$y_dim --pixels_in_x=$x_dim
mctf compress --always_B 0 --block_overlaping $block_overlaping --block_size $block_size --border_size $border_size --min_block_size $min_block_size --search_range $search_range --subpixel_accuracy $subpixel_accuracy --SRLs=$SRLs --GOPs=$GOPs --TRLs=$TRLs --slope=$slope --layers=$layers
mctf info --FPS=$FPS --GOPs=$GOPs --TRLs=$TRLs

mkdir tmp
mctf copy --GOPs=$GOPs --TRLs=$TRLs --destination="tmp"
cd tmp
mctf info --FPS=$FPS --GOPs=$GOPs --TRLs=$TRLs
mctf expand --block_overlaping $block_overlaping --block_size $block_size --border_size $border_size --min_block_size $min_block_size --search_range $search_range --subpixel_accuracy $subpixel_accuracy --SRLs=$SRLs --GOPs=$GOPs --TRLs=$TRLs
img=1
while [ $img -le $number_of_images ]; do
    _img=$(printf "%04d" $img)
    #let img_1=img-1
    img_1=$((img-1))
    _img_1=$(printf "%04d" $img_1)
    #convert -endian MSB L_0/${_img_1}_0.pgm /tmp/1.gray
    #(short2uchar < /tmp/1.gray > L_0/$_img.Y) 2> /dev/null
    #convert L_0/${_img_1}_0.pgm /tmp/1.gray
    #mv /tmp/1.gray L_0/$_img.Y
    input=L_0/${_img_1}_0.pgm
    output=L_0/$_img.Y
    PGMTORAW $input $output
    
    #convert -endian MSB L_0/${_img_1}_1.pgm /tmp/1.gray
    #(short2uchar < /tmp/1.gray > L_0/$_img.U) 2> /dev/null
    #convert L_0/${_img_1}_1.pgm /tmp/1.gray
    #mv /tmp/1.gray L_0/$_img.U
    input=L_0/${_img_1}_1.pgm
    output=L_0/$_img.U
    PGMTORAW $input $output
    
    #convert -endian MSB L_0/${_img_1}_2.pgm /tmp/1.gray
    #(short2uchar < /tmp/1.gray > L_0/$_img.V) 2> /dev/null
    #convert L_0/${_img_1}_2.pgm /tmp/1.gray
    #mv /tmp/1.gray L_0/$_img.V
    input=L_0/${_img_1}_2.pgm
    output=L_0/$_img.V
    PGMTORAW $input $output

    #let img=img+1
    img=$((img+1))
done
mctf psnr --file_A L_0 --file_B ../L_0 --pixels_in_x=$x_dim --pixels_in_y=$y_dim --GOPs=$GOPs --TRLs=$TRLs

(ffmpeg -y -s ${x_dim}x${y_dim} -pix_fmt yuv420p -i L_0/%4d.Y /tmp/out.yuv) > /dev/null 2> /dev/null || true
(mplayer /tmp/out.yuv -demuxer rawvideo -rawvideo w=$x_dim:h=$y_dim -loop 0 -fps $FPS) > /dev/null 2> /dev/null || true

mkdir transcode_quality
#mctf copy --GOPs=$GOPs --TRLs=$TRLs --destination="transcode_quality"
mctf transcode_quality_PLT --GOPs=$GOPs --TRLs=$TRLs --keep_layers=$keep_layers --destination="transcode_quality" --layers=$layers --slope=$slope
cd transcode_quality
mctf create_zero_texture --pixels_in_y=$y_dim --pixels_in_x=$x_dim
mctf info --GOPs=$GOPs --TRLs=$TRLs --FPS=$FPS
mctf expand --GOPs=$GOPs --TRLs=$TRLs
img=1
while [ $img -le $number_of_images ]; do
    _img=$(printf "%04d" $img)
    #let img_1=img-1
    img_1=$((img-1))
    _img_1=$(printf "%04d" $img_1)
    
    input=L_0/${_img_1}_0.pgm
    output=L_0/$_img.Y
    PGMTORAW $input $output
    
    input=L_0/${_img_1}_1.pgm
    output=L_0/$_img.U
    PGMTORAW $input $output
    
    input=L_0/${_img_1}_2.pgm
    output=L_0/$_img.V
    PGMTORAW $input $output

    #let img=img+1
    img=$((img+1))
done
mctf psnr --file_A L_0 --file_B ../L_0 --pixels_in_x=$x_dim --pixels_in_y=$y_dim --GOPs=$GOPs --TRLs=$TRLs

(ffmpeg -y -s ${x_dim}x${y_dim} -pix_fmt yuv420p -i L_0/%4d.Y /tmp/out.yuv) > /dev/null 2> /dev/null || true
(mplayer /tmp/out.yuv -demuxer rawvideo -rawvideo w=$x_dim:h=$y_dim -loop 0 -fps $FPS) > /dev/null 2> /dev/null || true

if [ $__debug__ -eq 1 ]; then
    set +x
fi
