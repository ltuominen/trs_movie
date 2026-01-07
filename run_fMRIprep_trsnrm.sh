np=0
maxjobs=2

tmp=$(find ../rawdata/ -maxdepth 1 -type d \( -name "sub-trs-012" -o -name "sub-trs510" \))
subjects=''
for t in ${tmp[@]}; do
b=$( basename $t )
subjects+=( ${b:4} )
done 

#--here we define fmriprep settings--#
bids_root_dir="/media/mrspecial/MrSpecialExtra/trsnrm"
nthreads=16
#--here we define fmriprep settings--#

for subject in ${subjects[@]}; do

docker run --rm -e DOCKER_VERSION_8395080871=27.0.2 -v /home/mrspecial/freesurfer/license.txt:/opt/freesurfer/license.txt:ro -v /media/mrspecial/MrSpecialExtra/trsnrm/rawdata:/data:ro -v /media/mrspecial/MrSpecialExtra/trsnrm/derivatives/iteration1:/out -v /media/mrspecial/MrSpecialExtra/trsnrm/SUBJECTS_DIR:/opt/subjects -v /media/mrspecial/MrSpecialExtra/fmriprepwork-trsnrm:/scratch nipreps/fmriprep:24.0.0 /data /out participant --participant-label "${subject}" --nthreads 16 --mem_mb 16000 --omp-nthreads 8 --verbose --fs-subjects-dir /opt/subjects -w /scratch --output-spaces MNI152NLin6Asym:res-2 anat

  # manage resources, run x jobs simultaneously
  (( np++ ))
  if [ $np == $maxjobs ]; then
  	 wait
  	 np=0
  fi
 
done
