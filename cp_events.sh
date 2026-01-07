file=/BICNAS2/tuominen/trsnrm/rawdata/sub-trs001/ses-001/func/sub-trs001_ses-001_task-rest_run-01_events.tsv

sublist=/BICNAS2/tuominen/trsnrm/rawdata/subs.txt

while read sub; do
	cp ${file} /BICNAS2/tuominen/trsnrm/rawdata/${sub}/ses-001/func/${sub}_ses-001_task-rest_run-01_events.tsv
        cp ${file} /BICNAS2/tuominen/trsnrm/rawdata/${sub}/ses-001/func/${sub}_ses-001_task-rest_run-02_events.tsv
done < ${sublist}

