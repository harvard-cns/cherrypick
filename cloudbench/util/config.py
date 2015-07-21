import os
import sys

if 'AZURE_STORAGE_KEY' not in os.environ or 'AZURE_STORAGE_NAME' not in os.environ:
    print >> sys.stderr, "You need to define AZURE_STORAGE_KEY and AZURE_STORAGE_NAME environment variables."
    #exit()


class Config(object):
    # Azure storage key, used by storage.azure_storage
    azure_storage_account_key = os.environ['AZURE_STORAGE_KEY']
    # Azure storage name, used by storage.azure_storage
    azure_storage_account_name = os.environ['AZURE_STORAGE_NAME']

    @staticmethod
    def path(*args):
        return os.path.abspath(os.path.join('..', *args))
