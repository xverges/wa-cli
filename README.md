# wa-cli: a CLI to enable programmer-friendly workflows for Watson Assistant skills

`wa-cli` is a command line tool that aims to make simple to:

* create individual developer/feature sandboxes for Watson Assistant skills
* enable peer reviews on skill changes by making them `git diff` and PR friendly
* have [Travis CI](https://travis-ci.com/) run dialog flow tests on changes

In the quest of the above goals, `wa-cli` has made easier some other tasks:

* decompose skill JSON files into diff friendly XML and CSV files
* clone the skills from a service to another service
* run k-fold and blind tests on a skill
* download, deploy, delete and get the training status of skills

`wa-cli` is mostly a thin wrapper that makes easier to use a subset of the features of

* [Watson Assistant Workbench](https://github.com/xverges/watson-assistant-workbench).
  This tool is able to perform a round-trip transformation of a JSON file exported
  from Watson Assistant into a set of CSV and XML files that make simpler version
  tracking and collaborative development. `wa-cli` relies on a fork of the
  [original repo](https://github.com/IBM/watson-assistant-workbench).
* [WA-Testing-Tool](https://github.com/cognitive-catalyst/WA-Testing-Tool).
  This tool can run several tests types on a Watson Assistant skill.
  `wa-cli` is able to use it to execute dialog flow testing (verify that a sequence
  of utterances get the expected output/intents/entities) and [k-fold
  testing](https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/kfold.md)
  to evaluate ground-truth consistency and generate [a confusion
  matrix](https://github.com/cognitive-catalyst/WA-Testing-Tool/blob/master/examples/confusion-matrix.md).

## Why

* Enable developers to use the Watson Assistant interface like a sort-of IDE,
  where you are fully aware of what you have changed, and you can go back to
  a known state of your changes, or have your changes peer-reviewed.
  This can be achieved with `wa-cli` sandboxes.
  [This project](https://github.com/xverges/wa-cli-demo) demonstrates the use
  of these sandboxes while following a Watson Assistant tutorial.
* Provide a simpler interface for the Watson Assistant API, [Watson Assistant
  Workbench](https://github.com/xverges/watson-assistant-workbench) and
  [WA-Testing-Tool](https://github.com/cognitive-catalyst/WA-Testing-Tool).

## Installing

This has only been tested on Python 3.8.1 on OSX, and Python 3.8.3 on Windows 10.
I created a conda environment with that version running `conda env create -f environment.yml`.

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

### Your project's `wa-cli`-related folders

These are the sub-folders in your `wa-cli`-managed WA project:

* `/skills`: where `wa-cli` downloads WA JSON skill files. Each of them is
  named `<skill-id>-<skill-name>.json`. You may choose to track them in git
  or `.gitignore` them.
* `/waw`: where the Watson Assistant Workbench disassembles the above files
  into diff-friendly XML and CSV files, and also where they are re-assembled
  before being deployed to WA.

  You'll find there a shared `re-assembled` folder (not kept under version
  control), and a `<skill-name>` folder for each of the skills that have been
  decomposed from JSON skill files.
* `/tests/kfold`: the reports resulting form `wa-cli skill test kfold <skill-file>`
  are written to `/tests/kfold/<skill-name>`.
* `/tests/flow`: the input files and the test reports resulting from
  `wa-cli skill test flow <skill-name>` or `wa-cli sandbox test`.
* `/.wa-cli`: where some configuration is stored, along with scripts used
  during travis builds.

### Sandboxes

A **sandbox** _branches_ a Watson Assistant skill: `wa-cli` creates a new skill
so that you can focus on developing a feature without being affected by the work
of others. While on the command line, you can be reminded of the workflow to use
by running `wa-cli sandbox | less`.

From your main git branch, you enable the use of sandboxes for a given skill:

```bash
(master) $ wa-cli sandbox enable SkillName
```

This command will download `SkillName` from Watson Assistant and decompose it
in `waw/SkillName`. These files need to be added and committed to git. You are
now ready to create a sandbox for the skill.

```bash
(master) $ git add waw
(master) $ git commit -m "Enabled sandboxes for SkillName"
(master) $ git checkout -b feature
(feature) $ wa-cli sandbox push SkillName
```

The last command will reassemble into a JSON skill file the files in `waw/SkillName`,
and create in Watson Assistant a skill named `feature_SkillName`. You can work with it
in the Watson Assistant UI. Whenever you want, you can download and inspect your changes:

```bash
(feature) $ wa-cli sandbox pull SkillName
(feature) $ git diff
```

Of course, you can commit your changes, or discard them, or edit the disassembled files
to fix typos or add intent examples... If you have updated the disassembled files, or have
reverted them to an earlier commit, you can push your changes to your sandbox again:

```bash
(feature) $ wa-cli sandbox push SkillName
```

When your feature is complete, you'll want to bring your changes to the main
project branch, probably using a Pull Request that can be peer reviewed. Once
the changes are in the main branch, you can delete the ad-hoc skill created in
order to develop the skill, and you'll need to deploy the feature to the main
skill:

```bash
(feature) $ wa-cli sandbox delete SkillName
(feature) $ git checkout master
(master) $ wa-cli sandbox deploy SkillName
```

### Testing

Your sandboxes can be tested. You can asses the consistency of your ground truth
with k-fold tests. This will run a k-fold test with 3 folds and display the confusion
matrix in your browser

```bash
(feature2) $ wa-cli sandbox test kfold SkillName --folds 3 --show-graphics
```

You can also run dialog flow tests. To run this, you need to create a file with
the expected output or intents or entities for sequence of utterances.
`wa-cli sandbox test flow --help` will provide additional information about the
format of test files, that need to be located in `test/flow/SkillName`.

```bash
(main) $ wa-cli sandbox test flow SkillName
```

### Travis

If you have created dialog flow tests, you may want to have travis execute them
on every Pull Request. To create the appropriate `.travis.yml` file, you can run

```bash
(main) $ wa-cli travis
```

After doing that, you still will need to setup github and travis.
