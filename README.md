# galaxy-tool-make-otu-table
A pipeline for clustering and making otu tables in galaxy. This repo has been adapted for Python3 and tested with Galaxy 19.09 Naturalis server. Older Galaxy releases are no longer supported.
## Getting Started
### Prerequisites

**USEARCH**<br />
(user: **galaxy**)\
\
A **USEARCH** license, which basically means you'll receive a download link after registration,\
can be obtained [here](https://www.drive5.com/usearch/download_academic_site.html) for university compute clusters. Paste the link in the **wget** command below.\
Be aware that the license has to be renewed each year.
```
mkdir /home/galaxy/Tools/usearch 
cd /home/galaxy/Tools/usearch
wget [your usearch licence]
mv [your usearch licence] usearch11
chmod 777 /home/galaxy/Tools/usearch/usearch11
```
(user: **ubuntu**)  
```
sudo ln -s /home/galaxy/Tools/usearch/usearch11 /usr/local/bin/usearch11
```
The following tools/packages are needed but included in the conda environment (make_otu_table_environment.yml)
* **VSEARCH**
* **R**
* **DADA2**
* **python3**
* **biopython**

### Installing  
(user: **galaxy**)  
Installing the tool for use in Galaxy
```
cd /home/galaxy/Tools
git clone https://github.com/naturalis/galaxy-tool-make-otu-table
chmod 777 galaxy-tool-make-otu-table/make_otu_table.py
```
Create the conda environment\
Make sure that _conda_group_ has permissions for all files recursively in at least `/opt/anaconda3/envs/`
```
sudo chgrp -R conda_group /opt
sudo chmod -R g+rwx /opt 
```

```
conda env create -f make_otu_table_environment.yml
```
Add the following line to /home/galaxy/galaxy/config/tool_conf.xml
(user: **galaxy**)
```
<tool file="/home/galaxy/Tools/galaxy-tool-make-otu-table/make_otu_table.xml" />
```
If you need to create the conda environment manually:
```
conda config --add channels conda-forge
conda config --add channels bioconda
conda config --add channels defaults
conda create -n __dada2env@1.14.0 -c conda-forge -c bioconda -c defaults --override-channels bioconductor-dada2=1.14.0 python=3.8.2 biopython=1.76 vsearch=2.14.2

```
Note: This installation shouldn't take long (at the end of March 2020 it took less than a minute)!
If you get 'found conflicts!' messages or it takes ages to install, something is wrong.
For this reason the anaconda package (which apparently was not a dependency) was also dropped.
## Workflow
On the following graph you can see the global workflow:
<br />

![flow](https://github.com/naturalis/galaxy-tool-make-otu-table/blob/master/img/make_otu_table.png)

<br />

### **1**
DADA2 is following a slightly different path. The file that is being used to do the analysis can be found here: https://github.com/naturalis/galaxy-tool-make-otu-table/blob/master/dada2.R
<br />
### **2**
Dereplication is done on one file containing all the sequences from the input zip file. With dereplication all duplicates will be removed and the amount(abundance) of the duplicates will be added to the fasta header. This abundance is needed for the other steps.
The command that is being used:
```
vsearch --derep_fulllength <combined_sequences.fa> --output <uniques.fa> --minseqlength 1 -sizeout
```
### **3**
The sequences will be sorted on abundance.
The command that is being used:
```
vsearch --sortbysize uniques.fa --output uniques_sorted.fa --minseqlength 1 --minsize <your min size>
```
### **4. UNOISE**
If the user choose UNOISE as clustering method UNOISE3 from the USEARCH package will be executed. This tool has build in chimera checking https://www.drive5.com/usearch/manual/cmd_unoise3.html.
The command that is being used:
```
usearch11 -unoise3 uniques_sorted.fa -unoise_alpha <alpha setting> -minsize <minimal abundance> -tabbedout cluster_file.txt -zotus zotususearch.fa
```
### **5. UPARSE**
If the user choose cluster_otus (UPARSE) as clustering method cluster_otus from the USEARCH package will be executed https://drive5.com/usearch/manual/cmd_cluster_otus.html. This tool clusters at a 97% identity and has build in chimera checking. 
The command that is being used:
```
usearch11 -cluster_otus uniques_sorted.fa -uparseout cluster_file.txt -otus otu_sequences.fa -relabel Otu -fulldp
```
### **6. VSEARCH uchime_denovo**
This tool is part of the VSEARCH package and it does chimera checking. If the users selects clustering with VSEARCH and with chimera checking this will be executed.
The command that is being used:
```
vsearch --uchime_denovo uniques_sorted.fa --sizein --fasta_width 0 --nonchimeras non_chimera.fa
```
### **7. VSEARCH cluster_size**
This tool is part of the VSEARCH package, it clusters at a certain identity that the user can set. This tool does not have build in chimera checking. And will be executed right after step 6.
The command that is being used:
```
vsearch --cluster_size non_chimera.fa --id <cluster identity> --sizein --fasta_width 0 --minseqlength 1 --relabel Otu --centroids otu_sequences.fa
```
### **8. VSEARCH cluster_size**
The user has the option to not check for chimeras, in this case only the command of step 7 will be executed.

### **9. VSEARCH UNOISE**
The UNOISE algorithm is also build in the VSEARCH package, the difference with UNOISE from the USEARCH package is that this one does not have build in chimera checking. So here we use tools from VSEARCH and first UNOISE is executed and afther that chimera checking is done.The command that is being used:
```
vsearch --cluster_unoise uniques_sorted.fa --unoise_alpha <alpha setting> --minsize <minimal abundance> --minseqlength 1 --centroids zotusvsearch.fa
```
### **10. VSEARCH uchime3_denovo**
Chimera checking on denoised reads with VSEARCH. The command that is being used:
```
vsearch --uchime3_denovo zotusvsearch.fa --fasta_width 0 --nonchimeras otu_sequences_nochime.fa
```
### **11. VSEARCH UNOISE**
The command that is being used:
vsearch --cluster_unoise uniques_sorted.fa --unoise_alpha <alpha setting> --minsize <minimal abundance> --minseqlength 1 --centroids zotusvsearch.fa
  
### **12. VSEARCH usearch_global**
After clustering the reads need to be mapped back on the otus to create an otu table. This tool is comming from the VSEARCH package but for some extra info you can vitis the following pages: https://drive5.com/usearch/manual/pipe_otutab.html and https://drive5.com/usearch/manual/mapreadstootus.html. The command that is being used:   
```
vsearch --usearch_global combined.fa --db otu_sequences.fa --id 0.97 --minseqlength 1 --otutabout otutab.txt --biomout bioom.json
```


## Source
Rognes T, Flouri T, Nichols B, Quince C, Mahé F. (2016) VSEARCH: a versatile open source tool for metagenomics. PeerJ 4:e2584. doi: 10.7717/peerj.2584

Edgar, R.C. (2016), UNOISE2: Improved error-correction for Illumina 16S and ITS amplicon reads.http://dx.doi.org/10.1101/081257

Edgar, R.C. (2013) UPARSE: Highly accurate OTU sequences from microbial amplicon reads, Nature Methods [Pubmed:23955772,  dx.doi.org/10.1038/nmeth.2604].
