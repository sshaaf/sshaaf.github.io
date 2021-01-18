---
title: number of lines of code in a directory
tags: [programming, linux, wc, find, code, shell]
date: 2010-10-29 15:25:39 +02:00
---




I just wanted to find the number of lines of java code in a directory i.e. recursively..


	find . -type f -name '*java' -print0 | wc -l --files0-from=-

	Output:
	.
	.
	56 ./App.java
	550 total
