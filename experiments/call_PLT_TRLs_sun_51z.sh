# DR_CURVE.SH
#//////////////

				
salta(){
	cd /home/cmaturana/scratch
	rm -rf $1
	mkdir $1
	cd $1
}
#/- sun ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


### 1 ##########################################################################

salta zero_sun_5TRL_1L
srun -N 1 -n 1 -p iball ../DRcurve.sh   -v  zero.yuv.avi                          -l  1  -b  128  -m  128  -g  9  -t  5  -y  4096  -x  4096  -f  0.027

exit 0
