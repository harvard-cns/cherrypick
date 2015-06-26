from cloudbench.env import Env
from cloudbench.util import Debug

import argparse, os
import multiprocessing

import traceback
import sys

BENCHMARK_PATH='../cloudbench/benchmarks/'

def run_benchmark_with_timeout(benchmark, env, timeout=5*60):
    # Each benchmark has a timeout to finish, this timeout
    # is either specified in the file or set to a default value
    # of 5 minutes
    if hasattr(benchmark, 'TIMEOUT'):
        timeout = benchmark.TIMEOUT

    def run(benchmark, env):
        try:
            benchmark.run(env)
        except Exception, err:
            print(traceback.format_exc())

    proc = multiprocessing.Process(target=run, args=(benchmark, env))
    proc.daemon = True
    proc.start()
    proc.join(timeout)

    if proc.is_alive():
        print "Timed out ... killing the process"
        proc.terminate()

    return timeout


def main():
    parser = argparse.ArgumentParser(prog='Cloudbench')

    parser.add_argument('--start', action='store_true',
        default=False, help='Start the VMs')

    parser.add_argument('--stop', action='store_true',
        default=False, help='Stop the VMs')

    parser.add_argument('--cloud', default="azure",
        help='Cloud provider')

    parser.add_argument('-s', '--setup', action='store_true',
        default=False, help='Prepares the benchmark environment')

    parser.add_argument('-t', '--teardown', action='store_true',
        default=False, help='Teardown the benchmark environment')

    parser.add_argument('-X', '--no-execute', action='store_true',
        default=False, help='Do not execute the benchmark')

    parser.add_argument('--test', action='store_true',
        default=False, help='Do not run anything, just print out the sequence of commands')

    parser.add_argument('--benchmark',
        help='Name of the benchmark that will be executed')

    parser.add_argument('-l', '--list', action='store_true',
        default=False, help='List all the benchmarks')

    parser.add_argument('--storage',
        default='azure', help='Storage to save the benchmark data.')

    parser.add_argument('-v', '--verbosity', action='count', default=0)

    args = parser.parse_args()

    Debug.verbosity(args.verbosity)

    if args.list:
        for directory in next(os.walk(BENCHMARK_PATH))[1]:
            print directory
        return

    if not os.path.exists(BENCHMARK_PATH + args.benchmark):
        print "Couldn't find the benchmark."
        return

    mod = __import__('cloudbench.benchmarks.' + args.benchmark + '.main',
                     fromlist=['cloudbench.benchmarks.' + args.benchmark])
    env = Env(args.cloud,
              BENCHMARK_PATH + args.benchmark + "/config.xml",
              args.benchmark,
              args.storage)

    if args.test:
        env.test(True)

    if args.setup:
        env.setup()

    if args.start:
        env.start()

    if not args.no_execute:
        run_benchmark_with_timeout(mod, env)

    if args.stop:
        env.stop()

    if args.teardown:
        env.teardown()
