#!/usr/bin/env python
"""

"""
import sys, os, argparse, string
import threading
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
                               help='Choice of clustering, usearch -cluster_otus or unoise', required=True, choices=['unoise', 'cluster_otus', 'vsearch', 'dada2','vsearch_unoise', 'vsearch_unoise_no_chimera_check', 'vsearch_no_chimera_check'])
requiredArguments.add_argument('-of', '--folder_output', metavar='folder output', dest='out_folder', type=str,
                               help='Folder name for the output files', required=True)
requiredArguments.add_argument('-a', '--unoise_alpha', metavar='unoise_alpha', dest='unoise_alpha', type=str,
                               help='unoise_alpha value', required=False, nargs='?', default="2.0")
requiredArguments.add_argument('-cluster_id', '--cluster_id', metavar='Minimal cluster identity percentage', dest='clusterid', type=str,
                               help='Minimal cluster identity percentage', required=False, nargs='?', default="97")
requiredArguments.add_argument('-cluster_size', '--cluster_size', metavar='Minimal cluster size', dest='clustersize', type=str,
                               help='Minimal cluster size', required=False, nargs='?', default="1")
requiredArguments.add_argument('-abundance_minsize', metavar='minimal abundance', dest='abundance_minsize', type=str,
                               help='unoise minsize', required=False, nargs='?', default="1")
args = parser.parse_args()

log_file_path = args.out_folder + "/log.log"

def check_if_fasta(file):
    log_write("Starting check_if_fasta", "make_otu_table.py", log_file_path)
    with open(file, "r") as handle:
        fasta = SeqIO.parse(handle, "fasta")
        return any(fasta)

def extension_check(outputFolder):
    log_write("Starting extension check", "make_otu_table.py", log_file_path)
    files = [os.path.basename(x) for x in sorted(glob.glob(outputFolder + "/files/*"))]
    fileFound = False
    for x in files:
        if args.input_type == "FASTQ":
            if os.path.splitext(x)[1].lower() == ".fastq" or os.path.splitext(x)[1] == ".fq":
                fastafile = os.path.splitext(x)[0].translate((str.maketrans("-. ", "___"))) + ".fa"
                error = Popen(["awk '{if(NR%4==1) {printf(\">%s\\n\",substr($0,2));} else if(NR%4==2) print;}' " + outputFolder + "/files/" + x + " > "+outputFolder+"/fasta/" + fastafile], stdout=PIPE, stderr=PIPE, shell=True).communicate()[1].strip()
                admin_log(outputFolder, error=error.decode(), function="extension_check")
                #add new line after last sequence
                call(["sed -i '$a\\' "+outputFolder+"/fasta/" + fastafile], shell=True)
                #Add sample name to fasta file like >[samplename].description
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + outputFolder + "/fasta/"+fastafile+" >> " + outputFolder + "/combined.fa"], shell=True)
                #DADA2 needs fastq files
                call(["cat " + outputFolder + "/files/"+x+" >> "+ outputFolder + "/combined_dada.fastq"], shell=True)
                fileFound = True
            else:
                log_write(x + "\nWrong extension, no fastq file (.fastq, .fq) file will be ignored. Please check if file extensions are correct and if your files are in the root of the zip file (not in sudirectories).", "ERROR:", log_file_path)
        else:
            if check_if_fasta(outputFolder + "/files/" + x):
                fastafile = os.path.splitext(x)[0].translate((str.maketrans("-. ", "___"))) + ".fa"
                call(["mv", outputFolder + "/files/" + x, outputFolder + "/fasta/" + fastafile])
                call(["sed -i '$a\\' " + outputFolder + "/fasta/" + fastafile], shell=True)
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + outputFolder + "/fasta/" + fastafile + " >> " + outputFolder + "/combined.fa"], shell=True)
                fileFound = True
            else:
                log_write("This is not a fasta file, file will be ignored", "ERROR:", log_file_path)
    process = Popen(["rm", "-rf", outputFolder + "/files"], stdout=PIPE, stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)
    if not fileFound:
        log_write("Tool stopped, no "+args.input_type+" files found", "ERROR:", log_file_path)
        exit()

def admin_log(outputFolder, out=None, error=None, function=""):
    with open(outputFolder + "/log.log", 'a') as adminlogfile:
        seperation = 60 * "="
        if out:
            adminlogfile.write(str(function) + " \n" + str(seperation) + "\n" + str(out) + "\n\n")
        if error:
            adminlogfile.write(str(function) + "\n" + str(seperation) + "\n" + str(error) + "\n\n")

def remove_files(outputFolder):
    log_write("Starting remove_files", "make_otu_table.py", log_file_path)
    call(["rm", "-rf", outputFolder+"/fasta"])
    if args.cluster != "dada2":
        call(["rm", outputFolder+"/combined.fa", outputFolder+"/uniques.fa"])
    if args.cluster == "dada2":
        call(["rm", outputFolder + "/combined_dada.fastq", outputFolder + "/combined_dada_filtered.fastq"])

def vsearch_derep_fulllength(outputFolder):
    log_write("Starting vsearch_derep_fulllength", "make_otu_table.py", log_file_path)
    #out, error = Popen(["vsearch", "--derep_fulllength", outputFolder+"/combined.fa", "--output", outputFolder+"/uniques.fa", "--minseqlength", "1", "-sizeout"], stdout=PIPE, stderr=PIPE).communicate()
    process = Popen(["vsearch", "--derep_fulllength", outputFolder + "/combined.fa", "--output", outputFolder + "/uniques.fa", "--minseqlength", "1", "-sizeout"], stdout=PIPE, stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

def usearch_cluster(outputFolder):
    log_write("usearch_cluster", "make_otu_table.py", log_file_path)
    #sort by size
    process = Popen(["vsearch", "--sortbysize", outputFolder+"/uniques.fa", "--output", outputFolder+"/uniques_sorted.fa","--minseqlength", "1","--minsize", args.abundance_minsize], stdout=PIPE, stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

    if args.cluster == "cluster_otus":
        process = Popen(["usearch11", "-cluster_otus", outputFolder+"/uniques_sorted.fa", "-uparseout", outputFolder+"/cluster_file.txt", "-otus", outputFolder+"/otu_sequences.fa", "-relabel", "Otu", "-fulldp"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

    if args.cluster == "unoise":
        process = Popen(["usearch11","-unoise3", outputFolder+"/uniques_sorted.fa", "-unoise_alpha", args.unoise_alpha, "-minsize", args.abundance_minsize, "-tabbedout", outputFolder+"/cluster_file.txt", "-zotus", outputFolder+"/zotususearch.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        count = 1
        with open(outputFolder + "/zotususearch.fa") as handle, open(outputFolder + "/otu_sequences.fa", 'a') as newotu:
            for record in SeqIO.parse(handle, "fasta"):
                newotu.write(">Otu" + str(count) + "\n")
                newotu.write(str(record.seq) + "\n")
                count += 1
        Popen(["rm", outputFolder + "/zotususearch.fa"])

    if args.cluster == "vsearch":
        process = Popen(["vsearch", "--uchime_denovo", outputFolder+"/uniques_sorted.fa", "--sizein", "--fasta_width", "0", "--nonchimeras", outputFolder+"/non_chimera.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        process = Popen(["vsearch", "--cluster_size", outputFolder+"/non_chimera.fa", "--id", args.clusterid, "--sizein", "--fasta_width", "0","--minseqlength", "1", "--relabel", "Otu", "--centroids", outputFolder+"/otu_sequences.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        call(["rm", outputFolder + "/non_chimera.fa"])

    if args.cluster == "vsearch_no_chimera_check":
        process = Popen(["vsearch", "--cluster_size", outputFolder+"/uniques_sorted.fa", "--id", args.clusterid, "--sizein", "--fasta_width", "0","--minseqlength", "1", "--relabel", "Otu", "--centroids", outputFolder+"/otu_sequences.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

    if args.cluster == "vsearch_unoise":
        process = Popen(["vsearch", "--cluster_unoise", outputFolder+"/uniques_sorted.fa", "--unoise_alpha", args.unoise_alpha,"--minsize", args.abundance_minsize,"--minseqlength", "1", "--centroids", outputFolder+"/zotusvsearch.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        process = Popen(["vsearch", "--uchime3_denovo", outputFolder+"/zotusvsearch.fa","--fasta_width", "0", "--nonchimeras", outputFolder + "/otu_sequences_nochime.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        count = 1
        with open(outputFolder + "/otu_sequences_nochime.fa") as handle, open(outputFolder + "/otu_sequences.fa", 'a') as newotu:
            for record in SeqIO.parse(handle, "fasta"):
                newotu.write(">Otu" + str(count) + "\n")
                newotu.write(str(record.seq) + "\n")
                count += 1
        Popen(["rm", outputFolder + "/otu_sequences_nochime.fa"])

    if args.cluster == "vsearch_unoise_no_chimera_check":
        process = Popen(["vsearch", "--cluster_unoise", outputFolder+"/uniques_sorted.fa", "--unoise_alpha", args.unoise_alpha,"--minsize", args.abundance_minsize, "--minseqlength", "1", "--centroids", outputFolder+"/zotusvsearch.fa"], stdout=PIPE, stderr=PIPE)
        process_name = process.args[0]
        process_streams(process, process_name, log_file_path)

        count = 1
        with open(outputFolder+"/zotusvsearch.fa") as handle, open(outputFolder + "/otu_sequences.fa", 'a') as newotu:
            for record in SeqIO.parse(handle, "fasta"):
                newotu.write(">Otu" + str(count) + "\n")
                newotu.write(str(record.seq) + "\n")
                count += 1
        Popen(["rm", outputFolder+"/zotusvsearch.fa"])

def dada2_cluster(outputFolder):
    ncount = 0
    with open(outputFolder + "/combined_dada.fastq") as handle, open(outputFolder +"/combined_dada_filtered.fastq", "a") as output:
        for record in SeqIO.parse(handle, "fastq"):
            if "N" in str(record.seq):
                ncount += 1
            else:
                output.write(record.format("fastq"))
    log_write("Sequences with N bases found and removed: "+str(ncount), "Remove N bases", log_file_path)

    process = Popen(["Rscript", "/srv/galaxy/local_tools/galaxy-tool-make-otu-table/dada2.R", outputFolder + "/combined_dada_filtered.fastq", outputFolder + "/otu_sequences.fa"], stdout=PIPE, stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

    #admin_log(outputFolder, out=out.decode(), error=error.decode(), function="dada2")

def usearch_otu_tab(outputFolder):
    process = Popen(["vsearch", "--usearch_global", outputFolder+"/combined.fa", "--db", outputFolder+"/otu_sequences.fa", "--id", "0.97", "--minseqlength", "1", "--otutabout", outputFolder+"/otutab.txt", "--biomout", outputFolder+"/bioom.json"], stdout=PIPE, stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

    #admin_log(outputFolder, out=out.decode(), error=error.decode(), function="otutab")

def zip_it_up(outputFolder):
    process = Popen(["zip","-r","-j", outputFolder+"/all_output.zip", outputFolder+"/"], stdout=PIPE, stderr=PIPE)

    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

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

# Function for writing data to a logfile.
def log_write(message, prefix, log_file):
    with open(log_file, 'a') as log:
        print(f"{prefix}: {message}") # show info in galaxy stdout/stderr output...
        log_line = f"{prefix}: {message}\n"
        log.write(log_line) #...as well as in a logfile.



# function for retrieving stdout/stderr logdata from a stream
def read_stream(stream, prefix, log_file):
    with open(log_file, 'a') as log:
        #log.write("\n\n##########################################\n\n")
        for line in iter(stream.readline, b''):
            decoded_line = line.decode().strip()
            print(f"{prefix}: {decoded_line}")
            log_line = f"{prefix}: {decoded_line}\n"
            log.write(log_line) # write retrieved data to logfile.

# function for starting threads for gathering stdout and stderr data of processes started with Popen()
# using threads for this function gives the benefit of receiving logs in realtime instead of after the process has completed.
def process_streams(process, process_name, log_file_path):
    # start log gathering from streams in a separate thread
    stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, f"{process_name} stdout", log_file_path))
    stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, f"{process_name} stderr", log_file_path))

    stdout_thread.start()
    stderr_thread.start()

    # "join" thread, meaning wait for treads to complete before continouing main script.
    stdout_thread.join()
    stderr_thread.join()

def main():
    outputFolder = args.out_folder
    make_output_folders(outputFolder)

    process = Popen(["unzip", args.inzip, "-d", outputFolder.strip() + "/files"], stdout=PIPE,stderr=PIPE)
    process_name = process.args[0]
    process_streams(process, process_name, log_file_path)

    extension_check(outputFolder)
    if args.cluster == "dada2":
        dada2_cluster(outputFolder)
    else:
        vsearch_derep_fulllength(outputFolder)
        usearch_cluster(outputFolder)
    usearch_otu_tab(outputFolder)
    remove_files(outputFolder)
    call(["cp", outputFolder + "/log.log", "/home/galaxy"])
    zip_it_up(outputFolder)

if __name__ == '__main__':
    main()
