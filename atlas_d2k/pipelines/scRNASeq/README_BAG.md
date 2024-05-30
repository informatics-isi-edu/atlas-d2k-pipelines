
# Download fastq bag

## Installation

Need to install bdbag (version 1.7.3) and deriva-py package (version 1.7.1)

```
pip install -U git+https://github.com/fair-research/bdbag
pip install -U git+https://@github.com/informatics-isi-edu/deriva-py
```

## Create a bdbag from config file
- use deriva-download-cli to create a bag with the following argument. Note that the bag will only contain the manifest of remote sequencing files, which can be materilize using a different command (see below).
  `--catalog <catalog number> <hostname> <config file> <directory> rid=<rid>`
  - `<config file>` contains bag configurations. Replicate_Input_Bag.json, Experiment_Input_Bag.json, and Study_Input_Bag.json contains the configurations for creating Replicate, Experiment, and Study bags, respectively.
  - `<directory>` is the directory where the bag will be created
  - `rid=<rid>` is the RID of Replicate, Experiment, or Study depending on the config file you use.

```
# Examples:
# for Replicate
> deriva-download-cli --catalog 2 www.atlas-d2k.org Replicate_Input_Bag.json . rid=16-2PS4

# for Experiment (W-RB4C, 16-X20M, 16-X20P)
> deriva-download-cli --catalog 2 www.atlas-d2k.org Experiment_Input_Bag.json . rid=W-RB4C

# for Study (e.g. W-RAHW, 16-WPBT)
>deriva-download-cli --catalog 2 www.atlas-d2k.org Study_Input_Bag.json . rid=W-RAHW
```
Note: Document can be found at https://docs.derivacloud.org/deriva-py/cli/deriva-download-cli.html#command-line-options

## Materialize bdbag
- Run the bdbag command with the unzipped bag as an argument to materialze the bag.
- All the data files will be created under `data` folder
- All the sequencing files will be materialized under `data/rnaseq` folder

```
# Example
> bdbag --materialize 16_2PS4_inputBag
```


