#!/usr/bin/python

import sys
import json
import csv
import os
from deriva.core import ErmrestCatalog, AttrDict, get_credential, DEFAULT_CREDENTIAL_FILE, tag, urlquote, DerivaServer, get_credential, BaseCLI, HatracStore
from deriva.core import urlquote, urlunquote
from deriva.core.ermrest_model import builtin_types, Schema, Table, Column, Key, ForeignKey, tag, AttrDict
from atlas_d2k.utils.data import get_entities
from atlas_d2k.utils.shared import AtlasD2KCLI, DCCTX
#from atlas_d2k.utils.hatrac import 
import requests.exceptions


scratch_dir = "/scratch/scrna"

''' Given a replicate
 - Create a metadata file in a tsv format?
 - Download replicate fastq files
'''


def get_experiment_settings(catalog, replicate_rid):
    experiment_settings = get_entities(catalog, "RNASeq", "Replicate", constraints="RID=%s/(Experiment_RID)=(RNASeq:Experiment_Settings:Experiment_RID)" % (urlquote(replicate_rid)) )
    
    print(json.dumps(experiment_settings, indent=4))

    return(experiment_settings[0])
    
# -- -----------------------------------------------------------------

def generate_hubmap_metadata(catalog, replicate_rid):
    template_fname = "rnaseq_template.tsv"
    template_file = open(template_fname, "r")
    #reader = csv.reader(template_file, delimiter="\t")
    #headers = next(reader)
    reader = csv.DictReader(template_file, delimiter="\t")
    defaults = next(reader)
    template_file.close()

    experiment_setting = get_experiment_settings(catalog, replicate_rid)
    
    metadata_fname = "%s_metadata.tsv" % (replicate_rid)
    tsvfile = open(metadata_fname, "w", newline="\n")
    writer = csv.DictWriter(tsvfile, fieldnames=defaults.keys(), delimiter="\t")
    writer.writeheader()
    writer.writerow(defaults)
    tsvfile.close()
    
# -- -----------------------------------------------------------------
def prepare_replicate_files(catalog, store, replicate_rid):
    replicate_dir = "%s/%s" % (scratch_dir, replicate_rid)
    # create dir structure
    os.makedirs("%s/extras" % (replicate_dir), exist_ok=True)
    fastq_dir = "%s/raw/fastq/RNA" % (replicate_dir)
    os.makedirs(fastq_dir, exist_ok=True)
    
    rows = get_entities(catalog, "RNASeq", "File", constraints="Replicate_RID=%s&File_Name::regexp::%s" % (urlquote(replicate_rid), urlquote(".[R][12].fastq.gz")) )
    json.dumps(rows, indent="4")
    
    for row in rows:
        file_path = "%s/%s" % (fastq_dir, row["File_Name"])
        local_file = store.get_obj(row["URI"], destfilename=file_path)
        print("Downloaded file: %s -> %s" % (row["URI"], file_path))


# -- =================================================================================
        
def main(server_name, catalog_id, credentials, args):
    server = DerivaServer('https', server_name, credentials)
    catalog = server.connect_ermrest(catalog_id)
    store = HatracStore("https", server_name, credentials)
    catalog.dcctx['cid'] = DCCTX["pipeline/seq/scrna"]
    model = catalog.getCatalogModel()

    if args.replicate:
        replicate_rid = args.replicate
    else:
        replicate_rid = "16-2PS4"
    
    #generate_hubmap_metadata(catalog, replicate_rid)
    get_experiment_settings(catalog, replicate_rid)
    prepare_replicate_files(catalog, store, replicate_rid)
    

# -- =================================================================================
# python -m atlas_d2k.pipelines.scRNASeq.prepare_replicate  --host dev.atlas-d2k.org --scratch /scratch/scrna --replicate 16-2PS4
if __name__ == '__main__':
    cli = AtlasD2KCLI("ATLAS-D2K", None, 1)
    cli.parser.add_argument('--scratch', metavar='<scratch>', help="scratch directory path", default=False)
    cli.parser.add_argument('--replicate', metavar='<replicate>', help="replicate rid", default=False)    
    args = cli.parse_cli()
    credentials = get_credential(args.host, args.credential_file)
    if args.scratch:
        scratch_dir = args.scratch
    main(args.host, args.catalog_id, credentials, args)
