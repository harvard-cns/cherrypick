class PackageManager(object):
    def __init__(self, vm):
        self.vm_ = vm
        super(PackageManager, self).__init__()

    def install(self, package):
        pass

    def remove(self, package):
        pass

    def installed(self, package):
        pass


class AptManager(PackageManager):
    def __init__(self, *args, **kwargs):
        super(AptManager, self).__init__(*args, **kwargs)
        self.updated_ = False

    def install(self, package):
        self.update()
        self.vm_.execute('sudo apt-get install %s -y' % package)
        return True

    def installed(self, package):
        self.vm_.execute('sudo dpkg-query -f -W \'${Status}\n %s' % package)
        return True

    def remove(self, package):
        self.update()
        self.vm_.execute('sudo apt-get remove %s -y' % package)
        return True

    def update(self):
        if not self.updated_:
            self.vm_.execute('sudo apt-get update -y')
            self.updated_ = True
