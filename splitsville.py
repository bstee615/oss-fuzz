"""Split a file of n lines into m jobs where each job i is n[i*m:i*(m+1)]"""

import argparse
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("data_file", type=Path, help="Data file to split.")
parser.add_argument("num_workers", type=int, help="Number of workers which are working concurrently.")
parser.add_argument("worker_id", type=int, help="Which worker am I?")
args = parser.parse_args()

with open(args.data_file) as f:
    data = f.readlines()
dataset_size = len(data)

normal_batch_size = math.ceil(dataset_size / args.num_workers)
my_batch_start = normal_batch_size * args.worker_id

batch = data[my_batch_start:my_batch_start+normal_batch_size]

for x in batch:
    print(x.strip())
