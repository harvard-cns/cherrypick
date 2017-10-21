import sys

from cherrypick_config import *
from schema import *

def machine_name(run):
    return run.config.machine.vm.name, run.config.count


if __name__ == '__main__':
    exp_name = EXPERIMENT
    if len(sys.argv) > 1:
        exp_name = sys.argv[1]
    exp = Experiment.find(exp_name)
    runs = filter_runs(exp.runs)
    runs = map(lambda x: (machine_name(x), COST_FUNC(x), x), runs)
    for run in sorted(runs, key=lambda x: -x[1]):
        print "\t".join(map(str, [run[0][0], run[0][1], run[1], run[2].cost, run[2].time]))
    exit(0)
    best_run = min(exp.runs, key=lambda x: COST_FUNC(x))
    print machine_name(best_run), COST_FUNC(best_run), best_run.cost
