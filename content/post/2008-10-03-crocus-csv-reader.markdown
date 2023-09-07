---
title: Crocus - CSV Reader
tags: [java, programming, software, csv, utils, how-to, api]
date: 2008-10-03 23:38:42 +02:00
---


Easy to use ready to go CSV File Reading utility. Read One or Multiple files into a RecordManager, quick access to the file with segmentation into Fields and Records. Merge Multiple CSV files in one. Listener to CSV Files.

[Download Here](https://sourceforge.net/project/platformdownload.php?group_id=172152)

Organization:
A CSV file is broken up as follows
A CSVField has a group of characters
A CSVRecord has a group of CSVFields
A CSVFile has a group of record

How To Use:

Reading a Single CSVFile into a RecordManager

```
	// Creating a single file interface
	CSVSingleFileInterface fileInterface = new CSVSingleFileInterface("/media/data/dev/workspace/crocus/testData/drupal-sample.csv",CSVConstants.COMMA);
	// Calling the read returns a CSVRecordManager i.e. in memory
	AbstractCSVRecordManager manager = fileInterface.read();
```

Reading multiple files into one RecordManager

```
	// Specify a FileSet
	AbstractCSVFileSet fileSet = new CSVFileSet();

	// Add files to the set
	fileSet.addFile("testData/drupal-sample.csv");
	fileSet.addFile("testData/countries.csv");

	// Add the fileSet to a Reading Interface
	CSVFileSetInterface fileSetInterface = new CSVFileSetInterface(fileSet);

	//  Reading returns a manager same as in a Single file case.
	AbstractCSVRecordManager manager = fileSetInterface.read();
```

This functionality is not complete but a peak is available.
You can now specify a Listener to Pre, Post and On Add of a record.

Setting up a Listener.

To add you listener simply implement the RecordListener class

```
	// Get a Record Manager
	AbstractCSVRecordManager manager = fileInterface.getRecordManager();

	// Add a listener to the Manager.
	manager.addRecordListener(this);
	// Implement an event listening method for listening to the RecordEvent.
	public void eventPerformed(RecordEvent recordEvent) {
	System.out.println(recordEvent.toString());

	}
```

The Build System:

The build script supports the following targets

Build: init, clean, compile, jar, javadoc, tests

Including, Excluding files while creating compile, jar, tests

FILE DETAILS (Paths and description):

PRE RULES:

---------

CROCUS_DEV = the main directory i.e. examples from here onwards this will be the variable used for describing details.

You will need to set CROCUS_DEV env variable inorder to run the build process

Also you would need to set ANT_HOME for usage of ant. I have used Ant 1.6.5 for builds.

$CROCUS_DEV/src Holds the source code i.e. java files

$CROCUS_DEV/build Carries all the build related files

$CROCUS_DEV/build/build.xml Main build script

$CROCUS_DEV/build/include.xml patterns for inclusion of java files at the time of compilation

$CROCUS_DEV/build/exclude.xml patterns for exclusion of java files at the time of compilation

$CROCUS_DEV/build/tests_include.xml patterns for inclusion of test java files at the time of compilation

$CROCUS_DEV/build/tests_exclude.xml patterns for exclusion of test java files at the time of compilation

$CROCUS_DEV/build/tools tools used during build.

$CROCUS_DEV/build/jar_buildfiles you can simply specify a txt file with some wild card matches and name it as yourjar.jar for the build system to recognize that "yourjar.jar" will be the name for this jar that should have the packages in it as specified in this txt(yourjar.jar)

$CROCUS_DEV/build/bin Holds the uniz script and the bat file for developers to run the build script more or less as:

Windows: %CROCUS_DEV%/build all

Linux: $CROCUS_DEV/build.sh all

$CROCUS_DEV/build_results Holds all the results of the builds

$CROCUS_DEV/build_results/docs Created java docs

$CROCUS_DEV/build_results/classes Created classes

$CROCUS_DEV/build_results/tests Unit test results

$CROCUS_DEV/build_results/jars the jars created by the system

$CROCUS_DEV/jars/ Is the directory for jars related information

$CROCUS_DEV/jars/manifests Holds the manifests for the $CROCUS_DEV/build/jar_buildfiles.

Conventionally should use: Manifest.jarName

$CROCUS_DEV/jars/original3rdparty Holds any 3rd party vendor jars that might be used for putting in the classpath for the build system

$CROCUS_DEV/testData logically should hold all testData no matter how that might be. currently I have placed a few csv files (tabbed,comma,semicolon).
