---
title: That thing about CI - Continous Integration
tags: [software, build, engineering, continous, ci, integration]
category: DevOps
date: 2008-11-12 14:11:18 +01:00
layout: post
type: post
---



Challenging Business requirements and the need for software development teams to remain agile and competitive while managing parallel development and releases requires a system which is adaptive to these demands.

Our approach to SCM enables unlimited and adaptable process models, which are ideally suited for parallel, distributed, and agile software development. Using state of the Art technologies from various vendors to automate processes such as branching, merging, build, and release keeps you a click away from software delivery.

The real matter then is the sanity of your application and that's the challenge we all need to address. We can have cute products right of the shelf to get it up and going but the whole challenge lies in the statement "up and going". It takes a ton of energy and effort to come up with the right process and the right tool. I have not seen alot of CI projects failing strictly. But I do have seen extra efforts into things that should not be really there. failure would then mean the amounts of efforts spent on doing not so trivial stuff and on the other end if you are spending alot of time doing the major flows then definately something is wrong.

Automation does solve most parts of the problems but things that really need to be taken care of to get it right in the sweet spot are the ones Martin Fowler described in one of his articles.

* *Maintain a Single Source Repository*
Keep everyone together, at the end of the day we all work together dont we?

* *Automate the Build*
Automation of the build helps you.

* *Make Your Build Self-Testing*
Self testing build tells you exactly what you did and what you broke. So I can come up with this statement to my Lead. "If I commit this, it might break alot of stuff". Well Sir, try running the Unit Test, You will know for sure! But then again honesty on the test cases really doest matter!

* *Everyone Commits Every Day*
Typically in a Agile environment helps alot, and forces you not to break the build. Better organization I must say.

* *Every Commit Should Build the Mainline on an Integration Machine*
Sanity checking of your commits. So often we commit without realiazing that we break something else.

* *Keep the Build Fast*
I usually commit before leaving for home. It helps great deal when you get the feedback within 5 mins. kind of a benchmark but depends.

* *Make it Easy for Anyone to Get the Latest Executable*
Keep all the build results and one sharable place. We did that on one of the http servers some time back

* *Everyone can see what's happening*
Importantly that all results are published for all of us to know.

* *Automate Deployment*
Deployment automation means that my buddy X on the other side doesnt screw up the server for even a 1 min. Only deploys when build successfull.

Hope this helps.

*Resources:*
http://martinfowler.com/articles/continuousIntegration.html
