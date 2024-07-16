---
title: wasprofile -create -delete
tags: [howto, java, programming, websphere, wsadmin, administrator, scripting, sysadmin, ibm, jython, jdbc, wasprofile]
date: 2008-10-24 13:38:00 +02:00
categories: ["Java"]
---



Sometimes you require to do things silently, without any questions asked and "Just Do It" attitude is required.

I often find my self with this problem.

If you want to delete or create a Websphere profile from your command line try the following. (I have tried on RSA only)

	# deleteing a profile
	wasprofile -delete -profileName MyProfile


You should get the following message on deletion

	INSTCONFSUCCESS: Success: The profile no longer exists.

Creating a websphere profile

	wasprofile -create -profileName MyProfile -profilePath \
	[PROFILE PATH] -templatePath \
	[RSA HOME]runtimes\base_v6\profileTemplates\default \
	-nodeName [NODE NAME] -cellName [CELL NAME] -hostName [HOSTNAME].
