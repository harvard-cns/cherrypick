for i in ../cloudbench/benchmarks/tmp_*; do
    echo $i;
    bench=$(echo $i | rev | cut -d'/' -f1 | rev)
    echo "Benchmark: $bench"

    if [ ! -z $i/aws.json ]; then
        ./cb --benchmark=$bench --cloud=aws --teardown --no-execute -vvvvv
    fi
done
