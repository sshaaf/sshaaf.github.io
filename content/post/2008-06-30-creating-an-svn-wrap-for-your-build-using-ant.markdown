---
title: Creating an SVN wrap for your build using Ant
tags: [howto, java, programming, scripting, svn, ant, build, automation]
date: 2008-06-30 14:45:32 +02:00
layout: post
type: post
---


Today after along break I would jump right on to one of the interesting topics in my den these days.

One of my friends was lately troubled with doing some SVN stuff like merging etc. And a lot of people will agree with me on their first experiences. :) I think.

While Automated builds take a lot of our time I thought I could plug in with some automated merging and a few other tasks. Its hard to go over all of that in one post but I will try putting in some basic stuff to get us started.

I call it the SVN Wrap.

Step 1.
Create a simple script file for wrapping svn and our environment.

A simple bat script could look like the following
	@echo off
	svn %*
However some people might want to add some environment variables to it. And that is where the strength of the this file comes in. You can tailor the environment dynamically!
e.g.

	set LC_ALL=C
	set SVN_HOME=svn-win32-1.4.6
	set PATH=%SVN_HOME%\bin;%PATH%;

FYI: By setting LC_ALL I am telling the system I disregard the default locale. Its just used as an example here. for more information

Refer to the svnbook at
[SVN Book](http://svnbook.red-bean.com/)

Step 2.
Create the build.xml
It doesnt get simpler then this.

I have created a project with the name CI-Test

	<project name="CI-Test" default="status" basedir=".">
		<description>
			This is a POC for SVN Wrap.
		</description>
	</project>



Importantly I am setting a property local.branch so that I can tell svn where my code has been checked out locally.

And finally the target that will take a status of the branch. for more details on the status command you could go here.

In general this target will give a general overview of the files and thier state at the moment.


	<target name="status">
		<echo message="Following is the status for this tree."/>
		<echo message="output is logged here: status.out" />
	          <exec dir="${local.branch}" executable="ci-svn.bat" output="status.out">
            		<arg line="status"/>
          	</exec>
	</target>


With in the target there are a few echo commands but the key construct is the exec.
The exec is going to do the following

dir="${local.branch}" - would meant execute the command in this directory
executable="ci-svn.bat" - Identifies the executable
and finally the output attribute to show where the output of this activity goes.
The following line will pass the parameters to the executable
arg line="status"
And in this case its sending a status command to svn.

For more details on exec goto.
[Apache Ant manual](http://ant.apache.org/manual/)


Now I would presume both these files in saved in one direcotry as

1. ci-svn.bat
2. build.xml

To run this simply goto your command console and once in the same directory execute by running
ant

It is assumed that all paths to java,ant and svn are set on your console or system.

As an output you should be able to see a status.out in the same directory from where you executed ant.

Hopefully this should get you started with doing some bit of svn commands from ant. And that just opens a lot of more possibilities in your build environment.

The complete code listing of the build file is as follows.

```
	<project name="CI-Test" default="status" basedir=".">
		<description>
			This is a POC for SVN Wrap.
		</description>

		<property name="local.branch" value="C:\branches\my-branch"/>

		<target name="status">
			<echo message="Following is the status for this tree."/>
			<echo message="output is logged here: status.out" />
	          	<exec dir="${local.branch}" executable="ci-svn.bat" output="status.out">
            			<arg line="status"/>
          		</exec>
		</target>
 	</project>
```
