for f in $(find build/out/ -name '*Fuzzer')
do
    python remove_target_class.py $f
done
