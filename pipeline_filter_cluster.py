#!/usr/bin/python
"""

"""
import sys, os, argparse
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
                               help='Choice of clustering, usearch -cluster_otus or unoise', required=True)
requiredArguments.add_argument('-o', '--output', metavar='output', dest='out', type=str,
                               help='output in zip format', required=True, nargs='?', default="")
requiredArguments.add_argument('-ol', '--output_log', metavar='output_log', dest='out_log', type=str,
                               help='output log file', required=True, nargs='?', default="")
requiredArguments.add_argument('-os', '--output_sequence', metavar='output_sequence', dest='out_seq', type=str,
                               help='output sequence file', required=True, nargs='?', default="")
requiredArguments.add_argument('-osz', '--output_sequence_size', metavar='output_sequence_size', dest='out_seq_size', type=str,
                               help='output sequence file with size annotation', required=True, nargs='?', default="")
requiredArguments.add_argument('-ot', '--output_table', metavar='output_table', dest='out_otu_table', type=str,
                               help='output otu table file', required=True, nargs='?', default="")
requiredArguments.add_argument('-oc', '--output_clusterfile', metavar='output_clusterfile', dest='out_cluster_file', type=str,
                               help='output cluster file', required=True, nargs='?', default="")
requiredArguments.add_argument('-ob', '--output_bioomfile', metavar='output_bioomfile', dest='out_bioom_file', type=str,
                               help='output bioom file', required=True, nargs='?', default="")
requiredArguments.add_argument('-a', '--unoise_alpha', metavar='unoise_alpha', dest='unoise_alpha', type=str,
                               help='unoise_alpha value', required=False, nargs='?', default="")


args = parser.parse_args()


def check_if_fasta(file):
    with open(file, "r") as handle:
        fasta = SeqIO.parse(handle, "fasta")
        return any(fasta)

def extension_check(tempdir):
    files = [os.path.basename(x) for x in sorted(glob.glob(tempdir + "/files/*"))]
    for x in files:
        if args.input_type == "FASTQ":
            if os.path.splitext(x)[1].lower() == ".fastq" or os.path.splitext(x)[1] == ".fq":
                fastafile = os.path.splitext(x)[0].replace(".", "_")+".fa"
                error = Popen(["awk '{if(NR%4==1) {printf(\">%s\\n\",substr($0,2));} else if(NR%4==2) print;}' " + tempdir + "/files/" + x + " > "+tempdir+"/fasta/" + fastafile], stdout=PIPE, stderr=PIPE, shell=True).communicate()[1].strip()
                admin_log(tempdir, error=error, function="extension_check")
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + tempdir + "/fasta/"+fastafile+" >> " + tempdir + "/combined.fa"], shell=True)
            else:
                admin_log(tempdir, error=x+"\nWrong extension, no fastq file (.fastq, .fq) file will be ignored", function="extension_check")
        else:
            if check_if_fasta(tempdir + "/files/" + x):
                fastafile = os.path.splitext(x)[0].replace(".", "_")+".fa"
                call(["mv", tempdir + "/files/" + x, tempdir + "/fasta/" + fastafile])
                call(["sed 's/>/>" + fastafile[:-3] + "./' " + tempdir + "/fasta/" + fastafile + " >> " + tempdir + "/combined.fa"], shell=True)
            else:
                admin_log(tempdir, error="This is not a fasta file, file will be ignored: " + x, function="extension_check")
    Popen(["rm", "-rf", tempdir + "/files"], stdout=PIPE, stderr=PIPE)



def admin_log(tempdir, out=None, error=None, function=""):
    with open(tempdir + "/adminlog.log", 'a') as adminlogfile:
        seperation = 60 * "="
        if out:
            adminlogfile.write("out "+ function + " \n" + seperation + "\n" + out + "\n\n")
        if error:
            adminlogfile.write("error " + function + "\n" + seperation + "\n" + error + "\n\n")

def remove_files(tempdir):
    call(["rm", "-rf", tempdir+"/fasta"])
    call(["rm", tempdir+"/combined.fa", tempdir+"/uniques.fa"])

def vsearch_derep_fulllength(tempdir):
    out, error = Popen(["vsearch", "--derep_fulllength", tempdir+"/combined.fa", "--output", tempdir+"/uniques.fa", "-sizeout"], stdout=PIPE, stderr=PIPE).communicate()
    admin_log(tempdir, out=out, error=error, function="derep_fulllength")

def usearch_cluster(tempdir):
    if args.cluster == "cluster_otus":
        out, error = Popen(["usearch10.0.240", "-cluster_otus", tempdir+"/uniques.fa", "-minsize", "2", "-uparseout", tempdir+"/cluster_file.txt", "-otus", tempdir+"/otu_sequences.fa", "-relabel", "Otu", "-fulldp"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(tempdir, out=out, error=error, function="cluster_otus")

    if args.cluster == "unoise":
        out, error = Popen(["usearch10.0.240","-unoise3", tempdir+"/uniques.fa", "-unoise_alpha", args.unoise_alpha, "-tabbedout", tempdir+"/cluster_file.txt", "-zotus", tempdir+"/zotususearch.fa", "-sizeout"], stdout=PIPE, stderr=PIPE).communicate()
        admin_log(tempdir, out=out, error=error, function="unoise")
        count = 1
        with open(tempdir + "/zotususearch.fa", "rU") as handle, open(tempdir + "/otu_sequences.fa", 'a') as newotu:
            for record in SeqIO.parse(handle, "fasta"):
                newotu.write(">Otu" + str(count) + "\n")
                newotu.write(str(record.seq) + "\n")
                count += 1
        Popen(["rm", tempdir + "/zotususearch.fa"])

def usearch_otu_tab(tempdir):
    out, error = Popen(["vsearch", "--usearch_global", tempdir+"/combined.fa", "--db", tempdir+"/otu_sequences.fa", "--id", "0.98", "--otutabout", tempdir+"/otutab.txt", "--biomout", tempdir+"/bioom.json"], stdout=PIPE, stderr=PIPE).communicate()
    admin_log(tempdir, out=out, error=error, function="otutab")

def zip_it_up(tempdir):
    call(["zip","-r","-j", tempdir+".zip", tempdir],stdout=open(os.devnull, 'wb'))
    call(["mv", tempdir + ".zip", args.out])

def send_output(tempdir):
    if args.out:
        zip_it_up(tempdir)
    if args.out_log:
        call(["mv", tempdir + "/adminlog.log", args.out_log])
    if args.out_seq:
        call(["mv", tempdir + "/otu_sequences.fa", args.out_seq])
    if args.out_otu_table:
        call(["mv", tempdir + "/otutab.txt", args.out_otu_table])
    if args.out_bioom_file:
       call(["mv", tempdir + "/bioom.json", args.out_bioom_file])



def main():
    tempdir = Popen(["mktemp", "-d", "/media/GalaxyData/files/XXXXXX"], stdout=PIPE, stderr=PIPE).communicate()[0].strip()
    print tempdir
    call(["mkdir", tempdir + "/fasta", tempdir + "/files"])
    zip_out, zip_error = Popen(["unzip", args.inzip, "-d", tempdir.strip() + "/files"], stdout=PIPE,stderr=PIPE).communicate()
    admin_log(tempdir, zip_out, zip_error)
    extension_check(tempdir)
    vsearch_derep_fulllength(tempdir)
    usearch_cluster(tempdir)
    usearch_otu_tab(tempdir)
    remove_files(tempdir)
    send_output(tempdir)
    call(["rm", "-rf", tempdir])


if __name__ == '__main__':
    main()

