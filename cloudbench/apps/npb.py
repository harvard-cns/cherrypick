def install(vm):
    vm.install('openmpi')
    vm.install('build-essential')
    vm.script('wget -rc -nd "https://www.nas.nasa.gov/assets/npb/NPB3.3.1.tar.gz"')
    vm.script('tar -xzf NPB3.3.1.tar.gz')
    vm.script('mv NPB3.3.1 npb')
    vm.script("sed -i '/^MPIF77/c\MPIF77=mpif77' npb/NPB3.3-MPI/config/make.def.template")
    vm.script('mv npb/NPB3.3-MPI/config/make.def.template npb/NPB3.3-MPI/config/make.def')
