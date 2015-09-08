from .azure import AzureCloud
from .aws import AwsCloud
from .gcloud import GcloudCloud
from .local import LocalCloud

__all__ = ['AzureCloud', 'AwsCloud', 'GcloudCloud', "LocalCloud"]
