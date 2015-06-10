import xml.etree.ElementTree as ET
from .base import EnvConfig

class EnvXmlConfig(EnvConfig):
    def __init__(self, f, cloud, env):
        super(EnvXmlConfig,self).__init__(f, cloud, env)

    def parse(self):
        self._tree = root = ET.parse(self._file)
        cloud = root.find(self._cloud)

        def parse_vms(this, cloud):
            for vm in cloud.findall('./virtual-machines/virtual-machine'):
                atts = vm.attrib

                for endpoint in vm.findall('./endpoint'):
                    ep = endpoint.attrib
                    if not 'endpoints' in atts:
                        atts['endpoints']  = []
                    atts['endpoints'].append(ep)
                this.add_virtual_machine(atts['name'], atts)

        def parse_groups(this, cloud):
            for gr in cloud.findall('./groups/group'):
                atts = gr.attrib
                this.add_group(atts['name'], atts)

        def parse_vnets(this, cloud):
            for vn in cloud.findall('./virtual-networks/virtual-network'):
                atts = vn.attrib
                this.add_virtual_network(atts['name'], atts)

        def parse_storages(this, cloud):
            for st in cloud.findall('./storages/storage'):
                atts = st.attrib
                this.add_virtual_network(atts['name'], atts)
        
        parse_groups(self, cloud)
        parse_vnets(self, cloud)
        parse_vms(self, cloud)
        parse_storages(self, cloud)


