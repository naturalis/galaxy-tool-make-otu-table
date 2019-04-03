# galaxy-tool-make-otu-table
A pipeline for clustering and making otu tables in galaxy. This repo can be used for the new (03-04-2019) galaxy 19.01 Naturalis server. The old galaxy 16.04 server is not supported anymore with this pipeline.
## Getting Started
### Prerequisites

**usearch**<br />
```
cd /home/galaxy/Tools/usearch
sudo wget [your usearch licence]
mv [your usearch licence] usearch11
sudo ln -s /home/galaxy/Tools/usearch/usearch11 /usr/local/bin/usearch11
```
**R**<br />
R is needed for DADA2, due to upgrading galaxy DADA2 is temporarly disabled. <br />
**DADA2**<br />
DADA2 is temporarly disabled.

### Installing
Installing the tool for use in Galaxy
```
cd /home/galaxy/Tools
```
```
sudo git clone https://github.com/naturalis/galaxy-tool-make-otu-table
```
```
sudo chmod 777 galaxy-tool-make-otu-table/make_otu_table.py
```
```
sudo ln -s /home/galaxy/Tools/galaxy-tool-make-otu-table/make_otu_table.py /usr/local/bin/make_otu_table.py
```
```
sudo cp galaxy-tool-make-otu-table/make_otu_table.sh /home/galaxy/galaxy/tools/identify/make_otu_table.sh
sudo cp galaxy-tool-make-otu-table/make_otu_table.xml /home/galaxy/galaxy/tools/identify/make_otu_table.xml
```
Add the following line to /home/galaxy/galaxy/config/tool_conf.xml
```
<tool file="identify/make_otu_table.xml" />
```
## Source
Rognes T, Flouri T, Nichols B, Quince C, Mahé F. (2016) VSEARCH: a versatile open source tool for metagenomics. PeerJ 4:e2584. doi: 10.7717/peerj.2584

Edgar, R.C. (2016), UNOISE2: Improved error-correction for Illumina 16S and ITS amplicon reads.http://dx.doi.org/10.1101/081257

Edgar, R.C. (2013) UPARSE: Highly accurate OTU sequences from microbial amplicon reads, Nature Methods [Pubmed:23955772,  dx.doi.org/10.1038/nmeth.2604].
