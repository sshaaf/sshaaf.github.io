---
title: How to read a file from the JAR?
tags: [howto, java, programming, software, software-development, utils, tips, jar]
date: 2008-10-31 20:57:54 +01:00
categories: ["Java"]
layout: post
type: post
---


Someone just asked me this question today. And I thought might as well put it down for info.

```
 	public TestReadFileFromJar() throws FileNotFoundException, IOException {
        	InputStream is = getClass().getResource("txtData/states.properties");
        	read(is);
	}
```

In the case above txtData is placed in the jar on the root. Remmember to add the path with the "/"
