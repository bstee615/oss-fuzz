for d in /run/media/benjis/BASILISK/Files/biggie/oss-fuzz/fuzz_10m_trace_3h/fuzz_run_5_complete/corpora-10m/*
do
    if [ ! -d corpora-10m/$(basename $d) ]
    then
        rsync -raP $d corpora-10m/
    fi
done