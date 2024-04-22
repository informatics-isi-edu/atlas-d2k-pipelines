################################################################################################
## Created:      2019/04/06
## Authors:      Animesh Kumar Singh Bhadouria, Hongsuda Tangmunarunkit
#################################################################################################

## Execute using 
## python3 -m atlas_d2k.cli.publication.export2bib.py --host dev.rebuildingakidney.org --consortium GUDMAP --from-year 2021 --to-year 2021


import argparse, calendar
# from datetime import datetime, timedelta
from deriva.core import DerivaServer, ErmrestCatalog, get_credential, write_credential
from deriva.core.ermrest_model import builtin_types, Table, Column, Key, ForeignKey
from atlas_d2k.utils.shared import DCCTX, AtlasD2KCLI

# Fetch month from timestamp
def getMonth( string ):
    if string is None:
        return None
    return calendar.month_abbr[ int ( string.split('-')[1] ) ]


def generatePublicationData(catalog, schema_name, table_name, consortium, from_year, to_year):
    # Fetch the table details
    #pathBuilder = catalog.getPathBuilder()    
    #publication_table = pathBuilder.schemas[args.schema_name].tables[args.table_name]
    #path = pub_table.path
    #dataset = list( path.filter( ( pub_table.Consortium == consortium) & (pub_table.Year == 2022) ) ).entities() )

    if not consortium: consortium = "any(GUDMAP,RBK)"
    query = "Consortium=%s&Curation_Status=Release&Year::geq::%s&Year::leq::%s@sort(Year::desc::,Month::desc::,Title)" % (consortium, from_year, to_year)
    resp = catalog.get("/entity/%s:%s/%s" % ("Common","Publication",query))
    dataset = resp.json()

    outfile = open( 'references.bib',mode = 'w', encoding='utf-8-sig', newline='\n' )
    outfile.write("---\n---\n")
    for data in dataset:
        outfile.writelines( "@article{ATLAS-D2K:"+ data["RID"] +",\n\t" )
        
        outfile.writelines( "title = {" + data["Title"] + "},\n\t")
        
        if data["Volume"] is not None:
            outfile.writelines( "volume = {" + str( data["Volume"] ) + "},\n\t" )

        if data["Issue"] is not None:
            outfile.writelines( "number = {" + data["Issue"] + "},\n\t" )

        if data["Pages"] is not None:
            outfile.writelines( "pages = {" + str( data["Pages"] ) + "},\n\t")

        if data["Abstract"] is not None:
            outfile.writelines( "abstract = {" + data["Abstract"] + "},\n\t")

        if data["Publication_Venue"] is not None:
            outfile.writelines( "journal = {" + data["Publication_Venue"] + "},\n\t")

        if data["Authors_List"] is not None:
            outfile.writelines( "author = {" + data["Authors_List"].replace(';', ' and') + "},\n\t")

        if data["Month"] is not None:
            outfile.writelines( "month = {" + str( data["Month"] ) + "},\n\t" )            
            #outfile.writelines( "month = "+ str( getMonth ( data['Release_Date'] ) ) + ",\n\t")

        outfile.writelines( "year = {" + str( data["Year"] ) + "},\n\t")

        # -- non-conventional
        if data["DOI"] is not None:
            outfile.writelines( "doi = {" + data["DOI"] + "},\n\t")

        if data["File_URL"] is not None:
            outfile.writelines( "url = {" + data["File_URL"] + "},\n\t")

        # use institution to be conventional
        outfile.writelines( "consortium = {" + data["Consortium"] + "},\n")
        
        outfile.writelines("}\n\n")
    
    # Close the output file
    outfile.close()



## Run the Script
if __name__ == "__main__":
    cli = AtlasD2KCLI("ATLAS-D2K", None, 1)
    cli.parser.add_argument('--protocol', help="default https", default="https", choices=["https", "http"] )
    cli.parser.add_argument('--schema-name', help="schema name", default="Common", choices=[ "Common" ] )
    cli.parser.add_argument('--table-name', help="table name", default="Publication", choices=[ "Publication" ]  )
    cli.parser.add_argument('--consortium', help="GUDMAP/RBK", default=None, choices=[ "GUDMAP", "RBK" ]  )
    cli.parser.add_argument('--from-year', help="From year (default=2023)", default=2023)
    cli.parser.add_argument('--to-year', help="To year (default=2023)", default=2023)
    
    args = cli.parse_cli()
    credentials = get_credential(args.host, args.credential_file)
    catalog = ErmrestCatalog( args.protocol, args.host, args.catalog_id, credentials)
    catalog.dcctx['cid'] = DCCTX["cli"]+"/export2bib"

    generatePublicationData(catalog, args.schema_name, args.table_name, args.consortium, args.from_year, args.to_year)
