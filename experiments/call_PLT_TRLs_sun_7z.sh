# DR_CURVE.SH
#//////////////

				
salta(){
	cd /home/cmaturana/scratch
	rm -rf $1
	mkdir $1
	cd $1
}
#/- sun ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

### 6 ##########################################################################
### 7 ##########################################################################

salta zero_sun_7TRL
srun -N 1 -n 1 -p iball ../DRcurve.sh   -v  zero.yuv.avi                          -l  8  -b  128  -m  128  -g  3  -t  7  -y  4096  -x  4096  -f  0.027





exit 0
