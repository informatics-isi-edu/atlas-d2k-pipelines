
## Generate Publication File ##
This function will will be used to generate "references.bib" file for:
- https://github.com/informatics-isi-edu/atlas-d2k-www


### Prerequisites
- deriva-py
```
$ pip install --upgrade git+https://github.com/informatics-isi-edu/deriva-py.git
```
- atlas-d2k module
```
$ pip install --upgrade git+https://github.com/informatics-isi-edu/atlas-d2k.git
```

### Description
References file can be generated using the below command.

- Execute using:
```
$ python3 -m atlas_d2k.cli.publication.export2bib --host dev.rebuildingakidney.org --consortium GUDMAP --from-year 2021 --to-year 2021

```
- Parameters:
    - host: Server Name to execute the script on. [ default = dev.gudmap.org ]
    - consortium: Used to extract publications for a specific source *GUDMAP* or *RBK* [ default = GUDMAP ]
    - from-year: The beginning of the publication year to export (inclusive). Default 2023. 
    - to-year: The end of the publication year to export (inclusive). Default 2023.   
    - protocol: Connection protocol. [ default = https ]
    - catalog: Catalog number. Default 2.
    - credential: Path to credential file. [ default = `~/.deriva/credential.json` ]