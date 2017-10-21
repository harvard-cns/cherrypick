import math

EXPERIMENT='tpcds'
COST_FUNC = lambda run: math.log(run.cost * 100)

def filter_runs(runs):
    def bad_runs(run):
        mt = {'large': 8, 'xlarge': 4, '2xlarge': 2}
        return run.config.count != mt[run.config.machine.vm.name.split(".")[1]]
    return filter(bad_runs, runs)
