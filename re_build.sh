export THREADS=4
# script for rebuilding storm + storm_py
ONLY_STORM=$1
if [ -z $ONLY_STORM ]
then
	cd storm/build && sudo cmake .. && sudo make storm-main storm-synthesis --jobs $THREADS && cd ../../stormpy && sudo python3 setup.py build_ext --jobs $THREADS develop && cd ../
else
	cd storm/build && sudo cmake .. && sudo make storm-main storm-synthesis --jobs $THREADS && cd ../../
fi	
