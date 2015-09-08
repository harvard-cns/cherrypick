from .base_storage import BaseStorage
from azure.storage.table import TableService, Entity
from cloudbench.util import Config, Debug

import sys

class AzureStorage(BaseStorage):
    def __init__(self, env):
        super(AzureStorage, self).__init__(env)
        self._ts = \
        TableService(
                account_name=Config.azure_storage_account_name,
                account_key=Config.azure_storage_account_key)

        self._benchmark = self._env.benchmark.name

        # Make sure our table exists
        Debug.info << "Creating tableservice for benchmark : " << \
            self.table_name() << "\n"

        self._ts.create_table(self.table_name())

    def table_name(self):
        return self._env.table_name

    def save(self, dic, partition=None, key=''):
        dic['RowKey'] = str(self.reverse_timestamp())
        dic['Cloud'] = str(self._env.cloud_name)

        if key:
            dic['RowKey'] = dic['RowKey'] + '_' + str(key)

        # Don't really need the partition key right now
        if partition is None:
            dic['PartitionKey'] = self._env.benchmark.name
        else:
            dic['PartitionKey'] = partition

        try:
            self._ts.insert_entity(self.table_name(), dic)
        except:
            print >> sys.stderr, "Error saving: %s" % dic
