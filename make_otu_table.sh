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
if [ $3 == "dada2" ]
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

usearch10.0.240 -otutab_stats $outlocation"/otutab.txt" -output $outlocation/"report.txt" 2>&1
echo "Otu table summary" >> $outlocation"/log.log"
echo "============================================================" >> $outlocation"/log.log"
cat $outlocation/"report.txt" >> $outlocation"/log.log" 

#output files
if [ $4 ] && [ -f $outlocation"/all_output.zip" ]
then
    mv $outlocation"/all_output.zip" $4
fi
if [ $5 ] && [ -f $outlocation"/log.log" ]
then
    mv $outlocation"/log.log" $5
fi
if [ $6 ] && [ -f $outlocation"/otu_sequences.fa" ]
then
    mv $outlocation"/otu_sequences.fa" $6
fi
if [ $7 ] && [ -f $outlocation"/otutab.txt" ]
then
    mv $outlocation"/otutab.txt" $7
fi
if [ $8 ] && [ -f $outlocation"/bioom.json" ]
then
    mv $outlocation"/bioom.json" $8
fi