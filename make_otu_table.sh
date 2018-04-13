#!/bin/bash

#location for production server
#outlocation=$(mktemp -d /media/GalaxyData/database/files/XXXXXX)
#location for the testserver
#outlocation=$(mktemp -d /media/GalaxyData/files/XXXXXX)

outlocation=$(mktemp -d /home/galaxy/ExtraRef/XXXXXX)
if [ $3 == "cluster_otus" ]
then
make_otu_table.py -i $1 -t $2 -c $3 -of $outlocation
fi
if [ $3 == "unoise" ]
then
make_otu_table.py -i $1 -t $2 -c $3 -of $outlocation -a ${9}
fi
if [ $3 == "vsearch" ]
then
make_otu_table.py -i $1 -t $2 -c $3 -of $outlocation -cluster_id ${9} -cluster_size "${10}"
fi

#output files
if [ $4 ]
then
    mv $outlocation"/all_output.zip" $4
fi
if [ $5 ]
then
    mv $outlocation"/log.log" $5
fi
if [ $6 ]
then
    mv $outlocation"/otu_sequences.fa" $6
fi
if [ $7 ]
then
    mv $outlocation"/otutab.txt" $7
fi
if [ $8 ]
then
    mv $outlocation"/bioom.json" $8
fi