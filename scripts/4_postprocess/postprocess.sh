#!/bin/bash

SAMPLE="--sample"
# SINGLE_THREAD="--single_thread"

# SAMPLE=""
SINGLE_THREAD=""

NPROC=6

INDIR="postprocessed_xmls/"
OUTFILE="postprocessed.jsonl"
python scripts/4_postprocess/2_main.py $INDIR $OUTFILE $SAMPLE $SINGLE_THREAD --nproc $NPROC

INFILE="$OUTFILE"
OUTFILE="${INFILE%.jsonl}_dedup.jsonl"
python scripts/4_postprocess/3_dedup_filter_examples.py $INFILE $OUTFILE

INFILE="$OUTFILE"
OUTFILE="${INFILE%.jsonl}_sort.jsonl"
python scripts/4_postprocess/4_sort_examples.py $INFILE $OUTFILE

python scripts/4_postprocess/8_filter_variables.py
