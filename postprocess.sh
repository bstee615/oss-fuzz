#!/bin/bash

# SAMPLE="--sample"
SAMPLE=""

NPROC=10

INDIR="/media/benjis/basilisk/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/repaired_xmls/"
OUTFILE="postprocessed/examples.jsonl"
python scripts/4_postprocess/2_exampleizer.py $INDIR $OUTFILE $SAMPLE --nproc $NPROC

INFILE="$OUTFILE"
OUTFILE="${INFILE%.jsonl}_dedup.jsonl"
python scripts/4_postprocess/3_dedup_filter_examples.py $INFILE $OUTFILE

INFILE="$OUTFILE"
OUTFILE="${INFILE%.jsonl}_sort.jsonl"
python scripts/4_postprocess/4_sort_examples.py $INFILE $OUTFILE
