#!/bin/bash

outlocation=$(mktemp -d /data/files/XXXXXX)
SCRIPTDIR=$(dirname "$(readlink -f "$0")")

# sanity check
printf "Conda env: $CONDA_DEFAULT_ENV\n"
printf "Outlocation: $outlocation\n"
printf "Python version: $(python --version |  awk '{print $2}')\n"
printf "Biopython version: $(conda list | egrep biopython | awk '{print $2}')\n"
printf "Usearch version: $(usearch11 | head -n1 | awk '{print $2}' | tr -d ',')\n"
printf "Vsearch version: $(conda list | egrep vsearch | awk '{print $2}')\n"
printf "Dada2 version: $(conda list | egrep dada2 | awk '{print $2}')\n"
printf "Unzip version: $(unzip -v | head -n1 | awk '{print $2}')\n"
printf "Bash version: ${BASH_VERSION}\n"
printf "SCRIPTDIR: $SCRIPTDIR\n\n"

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
if [ $3 == "vsearch_unoise_no_chimera_check" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -a ${9} -abundance_minsize "${10}"
fi
if [ $3 == "vsearch" ]
then
python $SCRIPTDIR"/make_otu_table.py" -i $1 -t $2 -c $3 -of $outlocation -cluster_id ${9} -abundance_minsize "${10}" -cluster_size "${11}"
fi
if [ $3 == "vsearch_no_chimera_check" ]
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

# Output Otu sequences as fasta file
if [ $6 ]
then
	cp $outlocation"/otu_sequences.fa" $6 && [ -f $outlocation"/otu_sequences.fa" ]
	# convert interleaved or multiline fasta to singleline
	cat $outlocation"/otu_sequences.fa" | 
	awk '/^>/ { if(NR>1) print "";  printf("%s\n",$0); next; } { printf("%s",$0);}  END {printf("\n");}' > $outlocation"/otu_sequences_DG.fa"
	rm $outlocation"/otu_sequences.fa"
	#------------------------------------------------------------------
	#  Adjust fasta headers to make them compatible with Otu-table.
	#  Files seem to be sorted, but sort anyway, just in case.
	#------------------------------------------------------------------
	# max length Otu label
	max_length=$(cat $outlocation"/otu_sequences_DG.fa"| egrep "^>Otu" | awk '{print length($1)}' | sort -n | uniq | tail -n1) 
	# max number of digits of Otu label (substract "Otu" from max_length Otu label)
	otu_digits=$(echo $max_length-4 | bc)
	# create a string of zeros 
	otu_digit_string=$(echo $(yes "0" | head -n "$otu_digits") | tr -d " ")
	# padding zeros
	cat $outlocation"/otu_sequences_DG.fa" | 
	sed "s/\(^>Otu\)\([0-9]\)/\1$otu_digit_string\2/g; s/0*\([0-9]\{$otu_digits,\}\)/\1/g" | paste - - | sort -n | sed 's/\t/\n/g' > 	$outlocation"/otu_sequences_DG2.fa"
	rm $outlocation"/otu_sequences_DG.fa"
	cp $outlocation"/otu_sequences_DG2.fa" $6 && [ -f $outlocation"/otu_sequences_DG2.fa" ]
fi


# Output Otu table
if [ $7 ]
then
	# it is not $7 that gets changed but the actual file ###.dat
	cp $outlocation"/otutab.txt" $7 && [ -f $outlocation"/otutab.txt" ]
	#------------------------------------------------------------------
	#  adjust Otu label format and sort
	#------------------------------------------------------------------
	# max length Otu label
	max_length=$(cat $outlocation"/otutab.txt" | egrep "^Otu" | awk '{print length($1)}' | sort -n | uniq | tail -n1) 
	# max number of digits of Otu label (substract "Otu" from max_length Otu label)
	otu_digits=$(echo $max_length-3 | bc)
	# create a string of zeros 
	otu_digit_string=$(echo $(yes "0" | head -n "$otu_digits") | tr -d " ")
	# padding zeros
	cat $outlocation"/otutab.txt" | sed "s/\(^Otu\)\([0-9]\)/\1$otu_digit_string\2/g; s/0*\([0-9]\{$otu_digits,\}\)/\1/g" | sort -n > $outlocation"/otutab_DG.txt"
	rm $outlocation"/otutab.txt"
	cp $outlocation"/otutab_DG.txt" $7 && [ -f $outlocation"/otutab_DG.txt" ]
fi

# OUtput Bioom file
if [ $8 ] && [ -f $outlocation"/bioom.json" ] && [ -f $outlocation"/bioom.json" ]
then
    mv $outlocation"/bioom.json" $8 && [ -f $outlocation"/bioom.json" ]
fi
rm -rf $outlocation
