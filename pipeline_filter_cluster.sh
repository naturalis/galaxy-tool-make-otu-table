#!/bin/bash
pipeline_filter_cluster.py -i $1 -t $2 -c $3 -o $4 -ol $5 -os $6 -osz $7 -ot $8 -oc $9 -ob "${10}" -a "${11}"







#while getopts i:t:c:o:ol:os:osz:ot:oc: option
#	do
#	case "${option}" in
#	i) INPUT=${OPTARG};;
#	t) INPUT_TYPE=${OPTARG};;
#	c) CLUSTER_COMMAND=${OPTARG};;
#	o) ZIP=${OPTARG};;
#	ol) LOG=${OPTARG};;
#	os) SEQUENCE=${OPTARG};;
#	osz) SEQUENCE_SIZE=$OPTARG;;
#	esac
#done
#pipeline_filter_cluster.py -i $INPUT -t $INPUT_TYPE -c "cluster_otus" -o $ZIP -ol $5 -os $LOG -osz $SEQUENCE_SIZE -ot -oc









