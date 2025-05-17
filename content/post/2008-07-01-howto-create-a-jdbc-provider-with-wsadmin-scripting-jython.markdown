---
title: HowTo create a JDBC provider with wsadmin scripting - Jython
tags: [howto, java, programming, websphere, wsadmin, administrator, scripting, sysadmin, ibm, jython, jdbc]
date: 2008-07-01 14:21:48 +02:00
layout: post
type: post
---


Last week I wrote a post about creating MQQueues with jacl. However today I am moving to Jython. This is the new scripting languauge supported by the wsadmin. The following write-up helps you create a JDBC provider using Jython in 6 easy steps on the wsadmin console.

*Pre requirements:
*Following should be known to start using this tutorial.

1. How to launch the wsadmin with Jython enabled.

*Where will I find the wsadmin?
*It is typically placed in the bin directory of your server.
In my case its lying in my RAD installation directory as
../Rational/SDP/6.0/runtimes/base_v6/bin

To invoke the wasadmin, just open your terminal and move to the bin dir where you can simply call it by typing wsadmin -lang jython. By doing so you would be invoking the default profile. if you want to specify the profile then use the switch -profileName YOURPROFILENAME

You can either paste the commands step by step or store the whole code listing in one file like DataSources.py. This means you can run this with wsadmin by specifying the -f switch.

After the wsadmin console is launched we can now move to creating the provider step by step.

*STEP 1.*
Identify classpath for the provider. This is a path to the jar files that need to be used by the provider. In our case its a jdbc dirver for oracle.

```
	driverPath = 'C:\lib\ojdbc14.jar'
```

*STEP 2.*
Identify the node and cell that will hold this provider. Node/Cell is how websphere is organized. As the Provider will be created inside a node we need to know which node we are working with.

```
	cellName=AdminControl.getCell()
	nodeName=AdminControl.getNode()
	node = AdminConfig.getid('/Cell:%s/Node:%s/' % (cellName,nodeName))
```

In the code above first we get the NodeName and CellName of the current connected server and then take the reference of it as node.

*STEP 3.
*Specify a template, In our case we have taken an 'Oracle JDBC Driver (XA)' template.
The following command will list the template for the provider specified and store it in a variable 'providerTemplate'

```
	providerTemplate=AdminConfig.listTemplates('JDBCProvider', 'Oracle JDBC Driver (XA)')
```

*STEP 4.
*The name for our provider. It could be any name you want to give your provider.

```
	providerName = ['name', 'Oracle JDBC Driver (XA)']
```

Implementation class and classpath for driver.
It is important to give the implementation class for our provider. In some cases they can be different in ours we use the default one.

```
	implClassName = ['implementationClassName', 'oracle.jdbc.xa.client.OracleXADataSource']
```

*STEP 5.*
The following code will just put all the above variables into a form expected by wsadmin as a temp variable jdbcAttrs.

```
	classpath = ['classpath',driverPath]
	jdbcAttrs = [providerName,  implClassName,classpath]
```

*STEP 6.*

Now is the time to create the provider. and the following will just do that. It passes the type of the provider, the node ref, the jdbcAttrs created in step 5 and the template to be used to create the provider.

```
	provider  = AdminConfig.createUsingTemplate('JDBCProvider', node, jdbcAttrs, providerTemplate)
	AdminConfig.save()
```

This is pretty much it. You should now be able to see the provider in the AdminConsole.

Complete code listing is as follows

```
	driverPath = 'C:\lib\ojdbc14.jar'
	cellName=AdminControl.getCell()
	nodeName=AdminControl.getNode()
	providerTemplate=AdminConfig.listTemplates('JDBCProvider', 'Oracle JDBC Driver (XA)')
	node = AdminConfig.getid('/Cell:%s/Node:%s/' % (cellName,nodeName))

	providerName = ['name', 'Oracle JDBC Driver (XA)']
	implClassName = ['implementationClassName', 'oracle.jdbc.xa.client.OracleXADataSource']
	classpath = ['classpath',driverPath]
	jdbcAttrs = [providerName,  implClassName,classpath]
	provider  = AdminConfig.createUsingTemplate('JDBCProvider', node, jdbcAttrs, providerTemplate)
	AdminConfig.save()
```
