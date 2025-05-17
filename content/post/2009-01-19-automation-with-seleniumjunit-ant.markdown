---
title: Automation with Selenium,Junit, Ant
tags: [software, ant, build, engineering, continous, ci, integration, scm, selenium, testing, automated-testing, junit]
date: 2009-01-19 16:31:52 +01:00
layout: post
type: post
---




[What is Selenium]:("http://seleniumhq.org")
[How does Selenium work]:("http://seleniumhq.org/about/how.html")
[History and how it started]:("http://seleniumhq.org/about/history.html")
[About Ant]:("http://ant.apache.org/")
[About Junit]:("http://www.junit.org/")


Much of the technologies above do not or will not need an introduction if you already know them or can read them from the links above.

More over today's article is more about how we can use all the three selenium, ant and junit to come up with an automated solution for regressive testing.

Please refer to the documentation links above for the basic knowledge on any of the used tools.

I am assuming that you know how to record a test in selenium if you dont then go
[here]:("http://selenium-ide.seleniumhq.org/)

Now that you do know how to record and save the tests simply save them in any directory structure you like as long as they follow the right package convention. like com.foo.bar
this would mean the file should be in directory like com/foo/bar. Conventionally and logically today that is how the TestCase is compiled through the ant script. If the package is not the right path then compile time errors will occur.

My calling target for running the whole procedure should look like this

	< target name="build_tests" depends="clean, compile, start-server,  tests, stop-server" / >


Details of the depending targets are as follows.
clean: would clean the entire build directories etc to make sure nothing from our past is carried forward into the future.

compile: should compile

start-server: should start the selenium server.

tests: should run the selenium tests.

stop-server: should stop the selenium server once all tests have been executed.

How to start a selenium server from Ant?

	< target name="start-server" >
        	< java jar="lib/selenium-server.jar" fork="true" spawn="true" >
            		< arg line="-timeout 30" / >
            		< jvmarg value="-Dhttp.proxyHost=proxy.proxyhost.com" / >
            		< jvmarg value="-Dhttp.proxyPort=44444" / >
        	< / java >
	< / target >


The target above is simply taking the selenium-server.jar which is in the classpath and running the main-class from it. the proxy parameters are optional.

How to stop the server from Ant?

	< target name="stop-server" >
        	< get taskname="selenium-shutdown"
    			src="http://localhost:4444/selenium-server/driver/?cmd=shutDown"
            		dest="result.txt" ignoreerrors="true" / >
        	< echo taskname="selenium-shutdown" message="DGF Errors during shutdown are expected" / >
	< / target >


The selenium server starts on port 4444 by default and to tell it to shutdown is simple, the command in the src is passed to it. cmd=shutDown
That should just shutdown the server.

Executing the test cases?
Selenium Test cases are Junit tests cases and that's how they are treated in this tutorial.
Thus some of you will be very much familiar with the ant targets

[Junit](http://ant.apache.org/manual/OptionalTasks/junit.html)
and
[junitreport](http://ant.apache.org/manual/OptionalTasks/junitreport.html)

However I will describe how the following is working. The following target will run the selenium tests and print a summary report to the ${dir}. The includes and excludes, simply tell the target which files to include or exclude while running the test cases. This is typically done when you don't want some tests cases to be included or your source for tests and the application are in the same directory and you only want to include something like *Test\*.class*.


	< target name="tests" depends="compileonly" description="runs JUnit tests" >
		< echo message="running JUnit tests" / >
		< junit printsummary="on" dir=".." haltonfailure="off" haltonerror="off" timeout="${junit.timeout}" fork="on" maxmemory="512m" showoutput="true" >
		< formatter type="plain" usefile="false" / >
		< formatter type="xml" usefile="true" / >
		< batchtest todir="${testoutput}" filtertrace="on" >
        	< fileset dir="${src}" >
          		< includesfile name="${tests.include}" / >
          		< excludesfile name="${tests.exclude}" / >
        	< / fileset >
      		< / batchtest >
      		< classpath >
        		< pathelement path="${classes}" / >
        		< pathelement path="${build.classpath}" / >
      		< / classpath >
    	< / junit >


The following will take the formatted output from the lines above and generate a report out of it in xml and html and place the results in the ${reports}/index.html
A sample Junit test report might look like
[this](http://studios.thoughtworks.com/cruise-continuous-integration/1.0/help/resources/images/cruise/tab-with-junit.png)

   < echo message="running JUnit Reports" / >
   < junitreport todir="${reports}" >
      < fileset dir="${reportdir}" >
        < include name="Test*.xml" / >
      < / fileset >
      < report format="frames" todir="${reports}" / >
    < / junitreport >
    < echo message="To see your Junit results, please open ${reports}/index.html}" / >
  < / target >


In general you can add all of this to your nightly build through any of the CI servers like Cruise Control. Also as a general practice you will need to do a  little more then just executing this target every night depending on your application. For instance cleaning up of resource centers like Databases etc.
