def input_type_filter(database):
    if database["cluster_algo"] == "dada2":
        options = [("FASTQ", "FASTQ", 1)]
    else:
        options = [("FASTQ", "FASTQ", 1), ("FASTA", "fasta", 2)]
    return options