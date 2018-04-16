#!/usr/bin/python
"""

"""
import sys, os, argparse, string
import glob
from Bio import SeqIO
from subprocess import call, Popen, PIPE

# Retrieve the commandline arguments
parser = argparse.ArgumentParser(description='')
requiredArguments = parser.add_argument_group('required arguments')

requiredArguments.add_argument('-i', '--input', metavar='input zipfile', dest='inzip', type=str,
                               help='Inputfile in zip format', required=True)
requiredArguments.add_argument('-t', '--input_type', metavar='FASTQ or FASTA input', dest='input_type', type=str,
                               help='Sets the input type, FASTQ or FASTA', required=True)
requiredArguments.add_argument('-c', '--cluster_command', metavar='otu or zotu(UNOISE)', dest='cluster', type=str,
                               help='Choice of clustering, usearch -cluster_otus or unoise', required=True, choices=['unoise', 'cluster_otus', 'vsearch'])
requiredArguments.add_argument('-of', '--folder_output', metavar='folder output', dest='out_folder', type=str,
                               help='Folder name for the output files', required=True)
requiredArguments.add_argument('-a', '--unoise_alpha', metavar='unoise_alpha', dest='unoise_alpha', type=str,
                               help='unoise_alpha value', required=False, nargs='?', default="2.0")
requiredArguments.add_argument('-cluster_id', '--cluster_id', metavar='Minimal cluster identity percentage', dest='clusterid', type=str,
                               help='Minimal cluster identity percentage', required=False, nargs='?', default="97")
requiredArguments.add_argument('-cluster_size', '--cluster_size', metavar='Minimal cluster size', dest='clustersize', type=str,
                               help='Minimal cluster size', required=False, nargs='?', default="1")
args = parser.parse_args()

def check_if_fasta(file):
    with open(file, "r") as handle:
        fasta = SeqIO.parse(handle, "fasta")
        return any(fasta)

def extension_check(outputFolder):
    files = [os.path.basename(x) for x in sorted(glob.glob(outputFolder + "/files/*"))]
    for x in files:
        if args.input_type == "FASTQ":
            if os.path.splitext(x)[1].lower() == ".fastq" or os.path.splitext(x)[1] == ".fq":
                fastafile = os.path.splitext(x)[0].translate((string.maketrans("-. ", "___"))) + ".fa"
                error = Popen(["awk '{if(NR%4==1) {printf(\">%s\\n\",substr($0,2));} else if(NR%4==2) print;}' " + outputFolder + "/files/" + x + " > "+outputFolder+"/fasta/" + fastafile], stdout=PIPE, stderr=PIPE, shell=True).communicate()[1].strip()
                admin_log(outputFolder, error=error, function="extension_check")
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + outputFolder + "/fasta/"+fastafile+" >> " + outputFolder + "/combined.fa"], shell=True)
            else:
                admin_log(outputFolder, error=x+"\nWrong extension, no fastq file (.fastq, .fq) file will be ignored", function="extension_check")
        else:
            if check_if_fasta(outputFolder + "/files/" + x):
                fastafile = os.path.splitext(x)[0].translate((string.maketrans("-. ", "___"))) + ".fa"
                call(["mv", outputFolder + "/files/" + x, outputFolder + "/fasta/" + fastafile])
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + outputFolder + "/fasta/" + fastafile + " >> " + outputFolder + "/combined.fa"], shell=True)
            else:
                admin_log(outputFolder, error="This is not a fasta file, file will be ignored: " + x, function="extension_check")
    Popen(["rm", "-rf", outputFolder + "/files"], stdout=PIPE, stderr=PIPE)

def admin_log(outputFolder, out=None, error=None, function=""):
    with open(outputFolder + "/log.log", 'a') as adminlogfile:
        seperation = 60 * "="
        if out:
            adminlogfile.write(function + " \n" + seperation + "\n" + out + "\n\n")
        if error:
            adminlogfile.write(function + "\n" + seperation + "\n" + error + "\n\n")

def remove_files(outputFolder):
    call(["rm", "-rf", outputFolder+"/fasta"])
    call(["rm", outputFolder+"/combined.fa", outputFolder+"/uniques.fa"])

def vsearch_derep_fulllength(outputFolder):
    out, error = Popen(["vsearch", "--derep_fulllength", outputFolder+"/combined.fa", "--output", outputFolder+"/uniques.fa", "-sizeout"], stdout=PIPE, stderr=PIPE).communicate()
    admin_log(outputFolder, out=out, error=error, function="derep_fulllength")

def usearch_cluster(outputFolder):
    if args.cluster == "cluster_otus":
        out, error = Popen(["usearch10.0.240", "-cluster_otus", outputFolder+"/uniques.fa", "-minsize", "2", "-uparseout", outputFolder+"/cluster_file.txt", "-otus", outputFolder+"/otu_sequences.fa", "-relabel", "Otu", "-fulldp"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(outputFolder, out=out, error=error, function="cluster_otus")

    if args.cluster == "unoise":
        out, error = Popen(["usearch10.0.240","-unoise3", outputFolder+"/uniques.fa", "-unoise_alpha", args.unoise_alpha, "-tabbedout", outputFolder+"/cluster_file.txt", "-zotus", outputFolder+"/zotususearch.fa"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(outputFolder, out=out, error=error, function="unoise")
        count = 1
        with open(outputFolder + "/zotususearch.fa", "rU") as handle, open(outputFolder + "/otu_sequences.fa", 'a') as newotu:
            for record in SeqIO.parse(handle, "fasta"):
                newotu.write(">Otu" + str(count) + "\n")
                newotu.write(str(record.seq) + "\n")
                count += 1
        Popen(["rm", outputFolder + "/zotususearch.fa"])

    if args.cluster == "vsearch":
        out, error = Popen(["vsearch", "--uchime_denovo", outputFolder+"/uniques.fa", "--sizein", "--fasta_width", "0", "--nonchimeras", outputFolder+"/non_chimera.fa"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(outputFolder, out=out, error=error, function="vsearch uchime")
        out, error = Popen(["vsearch", "--cluster_size", outputFolder+"/non_chimera.fa", "--id", args.clusterid, "--sizein", "--sizeout", "--fasta_width", "0", "--relabel", "Otu", "--centroids", outputFolder+"/otu_sequences_vsearch.fa"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(outputFolder, out=out, error=error, function="vsearch cluster")
        call(["rm", outputFolder + "/non_chimera.fa"])
        remove_single_clusters(outputFolder)

def remove_single_clusters(outputFolder):
    otuCount = 0
    singletonCount = 0
    with open(outputFolder + "/otu_sequences.fa", "a") as otuFile:
        for record in SeqIO.parse(outputFolder+"/otu_sequences_vsearch.fa", "fasta"):
            size = str(record.description).split("size=")[1][:-1]
            if int(size) > int(args.clustersize):
                header = str(record.description).split(";size=")[0]
                otuFile.write(">"+str(header)+"\n"+str(record.seq)+"\n")
                otuCount += 1
            else:
                singletonCount += 1
    #write to log
    out = "Minimal otu size:" + str(3) + " \nOtu's:" + str(otuCount) + "\nSingletons:" + str(singletonCount)
    admin_log(outputFolder, out=out, function="cluster size filtering")
    call(["rm", outputFolder + "/otu_sequences_vsearch.fa"])

def usearch_otu_tab(outputFolder):
    out, error = Popen(["vsearch", "--usearch_global", outputFolder+"/combined.fa", "--db", outputFolder+"/otu_sequences.fa", "--id", "0.98", "--otutabout", outputFolder+"/otutab.txt", "--biomout", outputFolder+"/bioom.json"], stdout=PIPE, stderr=PIPE).communicate()
    admin_log(outputFolder, out=out, error=error, function="otutab")

def zip_it_up(outputFolder):
    out, error = Popen(["zip","-r","-j", outputFolder+"/all_output.zip", outputFolder+"/"], stdout=PIPE, stderr=PIPE).communicate()
    admin_log(outputFolder, out=out, error=error, function="zip_it_up")

def send_output(outputFolder):
    if args.out:
        zip_it_up(outputFolder)
    if args.out_log:
        call(["mv", outputFolder + "/adminlog.log", args.out_log])
    if args.out_seq:
        call(["mv", outputFolder + "/otu_sequences.fa", args.out_seq])
    if args.out_otu_table:
        call(["mv", outputFolder + "/otutab.txt", args.out_otu_table])
    if args.out_bioom_file:
        call(["mv", outputFolder + "/bioom.json", args.out_bioom_file])

def make_output_folders(outputFolder):
    """
    Output en work folders are created. The wrapper uses these folders to save the files that are used between steps.
    :param outputFolder: outputFolder path
    """
    call(["mkdir", "-p", outputFolder])
    call(["mkdir", outputFolder + "/files"])
    call(["mkdir", outputFolder + "/fasta"])

def main():
    outputFolder = args.out_folder
    make_output_folders(outputFolder)
    zip_out, zip_error = Popen(["unzip", args.inzip, "-d", outputFolder.strip() + "/files"], stdout=PIPE,stderr=PIPE).communicate()
    admin_log(outputFolder, zip_out, zip_error)
    extension_check(outputFolder)
    vsearch_derep_fulllength(outputFolder)
    usearch_cluster(outputFolder)
    usearch_otu_tab(outputFolder)
    remove_files(outputFolder)
    zip_it_up(outputFolder)

if __name__ == '__main__':
    main()

