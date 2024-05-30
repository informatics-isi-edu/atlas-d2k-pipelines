#!/usr/bin/python

import sys
import json
from deriva.core import ErmrestCatalog, AttrDict, get_credential, DEFAULT_CREDENTIAL_FILE, tag, urlquote, DerivaServer, get_credential, BaseCLI
from deriva.core.ermrest_model import builtin_types, Schema, Table, Column, Key, ForeignKey
from deriva.core import urlquote, urlunquote
import argparse

# define ddctx cid string
# 
DCCTX = {
    "model": "model/change",
    "acl" : "config/acl",
    "annotation" : "config/anno",
    "comment" : "config/comment",
    "pipeline" : "pipeline",
    "pipeline/image" : "pipeline/image",
    "pipeline/seq/scrna" : "pipeline/seq/scrna",
    "pipeline/seq/mrna" : "pipeline/seq/mrna",
    "pipeline/seq/st" : "pipeline/seq/st",    # spatial transcriptomics
    "pipeline/noid" : "pipeline/noid",        # obsolete
    "cli": "cli",
    "cli/read" : "cli/read",
    "cli/test": "cli/test",            # read-write    
    "cli/ingest": "cli/ingest",        # read-write
}

tag2name = {}
for key, value in tag.items():
    tag2name[value] = key
tag2name['tag:isrd.isi.edu,2016:ignore'] = "ignore"


class Config():
    host = None
    is_prod = False
    is_staging = False
    is_dev = False
    
    def __init__(self):
        pass
    
    def apply_hostname(self, host):
        self.host = host
        if host in ["www.atlas-d2k.org", "www.gudmap.org", "www.rebuildingakidney.org"]:
            self.is_prod = True
        elif host in ["staging.atlas-d2k.org", "staging.gudmap.org", "staging.rebuildingakidney.org"]:
            self.is_staging = True
        else:
            self.is_dev = True
            
    def print(self):
        print("host:%s, is_prod=%s, is_staging=%s, is_dev=%s" % (self.host, self.is_prod, self.is_staging, self.is_dev))

cfg = Config()

# -- =================================================================================
# -- add catalog_id as an optional argument with default for SMITE
# -- set default host to be SMITE dev server
class AtlasD2KCLI(BaseCLI):
    def __init__(self, description, epilog, version=None, hostname_required=False, config_file_required=False, catalog_id_required=False, rid_required=False):
        # -- need to set hostname_required to false to add --host to the arg list
        if version:
            super().__init__(description, epilog, version, hostname_required=False, config_file_required=False)
        else:
            super().__init__(description, epilog, hostname_required=False, config_file_required=False)
            
        self.remove_options(['--host', '--config-file'])
        self.parser.add_argument('--host', metavar='<host>', help="Fully qualified hostname (default=dev.atlas-d2k.org)", default="dev.atlas-d2k.org", required=hostname_required)
        self.parser.add_argument('--catalog-id', metavar='<id>', help="Deriva catalog ID (default=2)", default=2, required=catalog_id_required)
        self.parser.add_argument('--pre-print', action="store_true", help="print annotations before clear", default=False)
        self.parser.add_argument('--post-print', action="store_true", help="print anntoations after update", default=False)
        self.parser.add_argument('--dry-run', action="store_true", help="run the script without model.apply()", default=False)
    
    def parse_cli(self):
        global env
        args = super().parse_cli()

        cfg.apply_hostname(args.host)
        
        return args

# -- =================================================================================        
