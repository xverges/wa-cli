# wa-cli: a CLI to enable programmer-friendly workflows for Watson Assistant skills

`wa-cli` is a command line tool that aims to make simple to:

* create individual developer sandboxes for Watson Assistant skills
* decompose skill JSON files into diff friendly XML and CSV files
* clone the skills from a service to another service
* run k-fold tests on a skill file
* download, deploy and delete skills

`wa-cli` is mostly a thin wrapper that makes easier to use a subset of the features of

* [Watson Assistant Workbench](https://github.com/xverges/watson-assistant-workbench).
  This tool is able to transform a JSON file exported from Watson Assistant
  into a set of CSV and XML files that make simpler version tracking and
  collaborative development. `wa-cli` relies on a fork of the
  [original repo](https://github.com/IBM/watson-assistant-workbench).
* [WA-Testing-Tool](https://github.com/cognitive-catalyst/WA-Testing-Tool).
  This tool can run several tests types on a Watson Assistant skill.
  `wa-cli` is able to use it to execute [k-fold
  testing](https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/kfold.md)
  to evaluate ground-truth consistency and generate [a confusion
  matrix](https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/confusion-matrix.md)

## Why

* Enable developers to use the Watson Assistant interface like a sort-of IDE,
  where you are fully aware of what you have changed, and you can go back to
  a known state of your changes, or have your changes peer-reviewed.
  This can be achieved with `wa-cli` sandboxes.
  [This project](https://github.com/xverges/wa-cli-demo) demonstrates the use
  of these sandboxes while following a Watson Assistant tutorial.
* Provide a simpler interface for the WA API, [Watson Assistant
  Workbench](https://github.com/xverges/watson-assistant-workbench) and
  [WA-Testing-Tool](https://github.com/cognitive-catalyst/WA-Testing-Tool).
  This is still work in progress.

## Installing

This has only been tested on Python 3.8.1 on OSX. I created a conda environment
with that version running `conda env create -f environment.yml`.

<!-- markdownlint-disable MD014 -->
```bash
$ conda env create -f environment.yml
$ conda activate wa-cli
```

You can clone the repo or install directly from github. Once you have your
virtual environment activated,

* **Cloning**

  * Clone the repo
  * Switch to its folder
  * Run `pip install --editable .`

* Less tested alternative, **direct installation**

  * Run `pip install https://github.com/xverges/wa-cli/archive/master.zip`

## Getting started

Switch to the folder where you want to keep your data files and
execute `wa-cli init`. You will be prompted for your WA credentials,
that will be saved to a `.env` file so that you don't need to specify
them as command line parameters.

The `wa-cli` command provides help and command completion. Run `wa-cli env`
to get the command that you have to execute to enable command completion
and to set the variables that you provided when running `wa-cli init`. The
specific command completion syntax depends on your default shell, as defined
in `$SHELL`.

<https://github.com/xverges/wa-cli-demo> demonstrates the use of sandboxes
