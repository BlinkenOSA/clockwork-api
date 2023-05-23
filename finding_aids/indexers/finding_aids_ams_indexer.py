import json

import pysolr
from django.conf import settings

from isad.models import Isad


class FindingAidsAMSIndexer:
    """
    Class to index ISAD(G) records to Solr.
    """

    def __init__(self, isad_id, target='ams'):
      pass