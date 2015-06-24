import xml.etree.ElementTree as ET
import inflection

from .base import EnvConfig
from cloudbench.env.entity import Entity

class EnvXmlConfig(EnvConfig):
    def __init__(self, _file, cloud, env):
        """ Initialize the XML config reader """
        super(EnvXmlConfig, self).__init__(_file, cloud, env)
        self._tree = None

    def read_cloud_configuration(self):
        """ Read the cloud specific configuration from the <cloud> tag

        Configurations are in the <config> tag and can be used by
        prepending "config:" to the value of an attribute, e.g.:

        <virtual-machine type='config:small' />

        <azure>
            <config name='small' value='Small' />
        </azure>

        <aws>
            <config name='small' value='A0' />
        </aws>

        This would use value A0 for the type of the virtual-machine if
        the active cloud is AWS, or it would use Small if the cloud
        provider is Azure.
        """
        root = self._tree
        config = root.find(self._cloud)

        if config is None:
            return

        for conf in config.findall('config'):
            # Save the cloud specific configurations
            self.config(conf.attrib['name'], conf.attrib['value'])


    def _parse_group(self, path, func):
        """ Parses a group of items """
        for item in self._tree.findall(path):
            atts = item.attrib
            dic = {}
            for key, val in atts.iteritems():
                dic[key] = self.value(val)
            func(dic['name'], dic)

    def parse(self):
        """ Parse the configuration file

        Parsing is a three step process:

        1) Read the cloud specific configurations
        2) Read the topology specification
        3) Add the cloud specific configuration to the topology
        configuration.

        """
        self._tree = ET.parse(self._file)

        # 1) Read the cloud specific configurations
        self.read_cloud_configuration()

        for entity in Entity.entities():
            classify = inflection.camelize(inflection.singularize(entity))
            dasherize = inflection.dasherize(inflection.underscore(classify))
            pluralize = inflection.pluralize(dasherize)
            add_name  = 'add_' + inflection.underscore(dasherize)
            ext_name  = 'extend_' + inflection.underscore(dasherize)
            path = './' + pluralize + '/' + dasherize

            # 2) Parse topology specific configuration
            self._parse_group('./' + pluralize + '/' + dasherize,
                    getattr(self, add_name))

            # 3) Parse cloud specific configuration for topology
            self._parse_group('./' + self.cloud + '/' + pluralize + '/add-values',
                    getattr(self, ext_name))

        # print self.locations()
        # print map(lambda x: x.virtual_machines(), self.locations().values())
        # print map(lambda x: x.location(), self.virtual_machines().values())

        # for key, val in self._entities.iteritems():
        #     print val

        # for _, vm in self.virtual_machines().iteritems():
        #     print repr(vm)

