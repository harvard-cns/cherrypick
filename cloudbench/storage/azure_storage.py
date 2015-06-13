from .base_storage import BaseStorage
from azure.storage import TableService, Entity
from cloudbench.util import Config, Debug

class AzureStorage(BaseStorage):
    def __init__(self, env):
        super(AzureStorage, self).__init__(env)
        self._ts = \
        TableService(
                account_name=Config.azure_storage_account_name,
                account_key=Config.azure_storage_account_key)

        self._benchmark = self._env.benchmark_name()

        # Make sure our table exists
        Debug.info << "Creating tableservice for benchmark : " << \
            self.table_name() << "\n"

        self._ts.create_table(self.table_name())

    def table_name(self):
        return 'cloudbench'

    def save(self, dic, key=None):
        dic['RowKey'] = self.timestamp()

        # Don't really need the partition key right now
        if key is None:
            dic['PartitionKey'] = self._env.benchmark_name()
        else:
            dic['PartitionKey'] = key

        self._ts.insert_entity(self.table_name(), dic)
