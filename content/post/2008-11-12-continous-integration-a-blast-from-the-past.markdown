---
title: Continous Integration - A blast from the past
tags: [software, build, engineering, continous, ci, integration, scm]
date: 2008-11-12 20:00:16 +01:00
layout: post
type: post
---


Although this didn't happen a decade ago but still has been a good case for me to learn and realize how Continuous Integration brings value addition to our work.

As I recall it was like this when they were teenagers :D
Few teams working on different modules of same application, deployed together.
No build process formalized
No builds except for the ones that need major milestone deployments.
No feedback, reports, reviews etc.

So virtually there was no build eco system.

Which meant hideous amounts of communication, tons of trouble shooting, last minute show stoppers, And extermely unhappy end users/stake holders.

So what exactly was going wrong.

There was no Configuration Control i.e. No way to figure out the changes that will be part of the release and no controls to include or exclude them.
No Status accounting i.e. No feedback or status of anything as a whole product.
No management of Environment meant no one knew what hardware/software they were using and sometimes why?
No team work whatsoever meant no guided processes, reviews or tracebility of issues and pitfalls.

So virtually a release day was the doomsday!


It took some time for developers to realize that how important the following were.

    * Configuration identification - What code are we working with?

    * Configuration control - Controlling the release of a product and its changes.

    * Status accounting - Recording and reporting the status of components.

    * Review - Ensuring completeness and consistency among components.

    * Build management - Managing the process and tools used for builds.

    * Process management - Ensuring adherence to the organization's development process.

    * Environment management - Managing the software and hardware that host our system.

    * Teamwork - Facilitate team interactions related to the process.

    * Defect tracking - Making sure every defect has traceability back to the source

And after all it takes some time but the day to day flow looked like the figure below.
![Alt text](/images/2008/11/build-300x221.png)

[Download Image] (/images/2008/11/build.png)

Importantly
	+ Developers are distributed on different locations in different teams.
	+ There is an SCM team that takes care of the SCM activities i.e. Configuration Identification, Control, Build Management etc.
	+ There is one single repository for all developers.
	+ A process is defined for Product integration and its checked whenever some one checks in.
	+ And hourly build is dont to check the sanity of the system with the unit tests.
	+ A Nightly build is done with all full blown unit tests, coverage reports, Automated tests and installers and upgrades.
	+ More over all of the above is shown on an FTP/HTTP site. FTP for installer/binary/archive pickup and HTTP for detailed view of builds/feedbacks etc.

All of the above meant strength and health of the build eco system. And more trust in the system that it will report failures along the way.
