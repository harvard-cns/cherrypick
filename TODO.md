# TODO List

1) If a virtual machine cannot be started, we should detect it; this has
happened to me several times when in Azure, the virtual-machine does not
start because of resource constraints.

2) Can we start the virtual-machine only when we need it?  If we do
that, when would we stop the VM?  Can we detect this?  Maybe having a
class that automates execution of benchmarks would be useful .. i.e.,
the benchmark script would _submit_ jobs to the executor, and executor
would run the benchmarks.

3) Make the tool installation/benchmarks agnostic.  Right now, we are
creating benchmarks per tool, which is actually not we want ... a tool
should be *contained* by itself, so that it can be used in different
scenarios -- and get automatically installed by the virtual-machine if
it was required for a specific benchmark.  Thoughts?
