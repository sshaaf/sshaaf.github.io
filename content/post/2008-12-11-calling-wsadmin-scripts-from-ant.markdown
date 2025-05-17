---
title: Calling wsadmin scripts from ant
tags: [howto, java, programming, websphere, wsadmin, administrator, scripting, sysadmin, ibm, ant, jython, jdbc, script]
date: 2008-12-11 10:17:46 +01:00
layout: post
type: post
---



You can simply add the following to a target.
For the following wsadmin should be in your PATH env.

	< exec dir="." executable="wsadmin.bat" logError="true" failonerror="true" output="wsconfig.out" >
   		< arg line="-lang jython -f ../../createQFactory.py"/ >
	< /exec >


All output will be logged to wsconfig.out
