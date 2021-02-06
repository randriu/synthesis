function cav() {
    mkdir -p $log_dir/cav

    timeout=7d
    # parallel=true

    dpm=("cav/dpm" 10 140 140 1.0)
    maze=("cav/maze" 0 7.32 7.32 1.0)
    herman=("cav/herman" 0 3.5 3.5 1.0)
    pole=("cav/pole" 0 16.6566 16.6566 1.0)
    grid=("cav/grid" 40 0.928 0.928 1.0)

    optimal=false
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/hybrid_f_$model.txt
        hybrid $model
    done
    optimal=true
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/hybrid_0_$model.txt
        hybrid $model
    done
    optimal=true
    for model in dpm maze herman pole grid; do
        log_file=$log_dir/cav/onebyone_$model.txt
        onebyone $model &
    done
    wait
}

function cav_summary() {
    for log in $log_dir/cav/*.txt; do
        echo "--- ${log} --"
        head $log -n 100 >> ${log}_2
        tail $log -n 100 >> ${log}_2
        mv ${log}_2 ${log}
        cat $log | tail -n 12
    done
}