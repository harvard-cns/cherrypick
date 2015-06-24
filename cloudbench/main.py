from cloudbench.env import Env
from cloudbench.util import Debug
import argparse, os

BENCHMARK_PATH='../cloudbench/benchmarks/'

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

    if args.setup:
        env.setup()

    if args.start:
        env.start()

    if not args.no_execute:
        mod.run(env)

    if args.stop:
        env.stop()

    if args.teardown:
        env.teardown()
