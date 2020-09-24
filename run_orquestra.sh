#!/bin/bash

# call as run_orquestra my_workflow.yaml

echo "Running for Workflow $1"

out=$(qe submit workflow $1)
echo $out
ID=$(echo $out | grep "Workflow ID" | cut -d ':' -f 2| sed 's/ //g') 
echo $ID

out=$(qe get workflowresult $ID)

state="run"
while [[ $state == "run" ]]; do
     
	if [[ $out =~ "http" ]]
	then
		echo "finished"
		state="exit"
		break
	else
		echo $(qe get workflow $ID)
                echo "not finished yet"	
	fi
        sleep 10 # maybe adapt for other workflows
	out=$(qe get workflowresult $ID)
done
echo "exited with $out"
url=$(qe get workflowresult $ID | awk -F 'Location:' '{print $2}' | sed 's/ //g')

echo "results are located at: $url"
echo "Downloading results"

wget -O "result_$ID.json" $url

python evaluate_workflow_result.py filename="result_$ID.json"
