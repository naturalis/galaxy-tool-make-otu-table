#!/bin/bash

outlocation=$(mktemp -d /home/galaxy/galaxy/database/XXXXXX)
SCRIPTDIR=$(dirname "$(readlink -f "$0")")

if [ $3 == "cluster_otus" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -abundance_minsize "${9}"
fi
if [ $3 == "dada2" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation
fi
if [ $3 == "unoise" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -a ${9} -abundance_minsize "${10}"
fi
if [ $3 == "vsearch_unoise" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -a ${9} -abundance_minsize "${10}"
fi
if [ $3 == "vsearch" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -cluster_id ${9} -abundance_minsize "${10}" -cluster_size "${11}"
fi

#usearch11 -otutab_stats $outlocation"/otutab.txt" -output $outlocation/"report.txt" &> /dev/null
#echo "Otu table summary" >> $outlocation"/log.log"
#echo "============================================================" >> $outlocation"/log.log"
#cat $outlocation/"report.txt" >> $outlocation"/log.log"

#output files
if [ $4 ]
then
    mv $outlocation"/all_output.zip" $4 && [ -f $outlocation"/all_output.zip" ]
fi
if [ $5 ]
then
    mv $outlocation"/log.log" $5 && [ -f $outlocation"/log.log" ]
fi
if [ $6 ]
then
    mv $outlocation"/otu_sequences.fa" $6 && [ -f $outlocation"/otu_sequences.fa" ]
fi
if [ $7 ]
then
    mv $outlocation"/otutab.txt" $7 && [ -f $outlocation"/otutab.txt" ]
fi
if [ $8 ] && [ -f $outlocation"/bioom.json" ] && [ -f $outlocation"/bioom.json" ]
then
    mv $outlocation"/bioom.json" $8 && [ -f $outlocation"/bioom.json" ]
fi
rm -rf $outlocation
