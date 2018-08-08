list.of.packages <- c("dada2")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages)

library(dada2)

args = commandArgs(trailingOnly=TRUE)
if (length(args)==0) {
  stop("At least one argument must be supplied", call.=FALSE)
} else if (length(args)==1) {
  # default output file
  args[2] = "otu_sequences.fa"
}

path <- args[1]
#fnFs <- list.files(path, full.names = TRUE)
fnFs <- args[1]
errF <- learnErrors(fnFs, multithread=TRUE)
derepFs <- derepFastq(fnFs, verbose=TRUE)
dadaFs <- dada(derepFs, err=errF, multithread=TRUE)
i<-0
for(seq in dadaFs$sequence){
i<-i+1
write(c(paste(">Otu",toString(i),sep="")),file=args[2],append=TRUE)
write(c(paste(seq)),file=args[2],append=TRUE)
}

