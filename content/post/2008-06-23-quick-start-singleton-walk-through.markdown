---
title: Quick start Singleton - Walk through
tags: [computers, design, design-patterns, gof, howto, java, patterns, programming, singleton, singleton-pattern, software, software-development]
category: Software Design
date: 2008-06-23 03:56:37 +02:00
---


This being my first existence on the network and I just want to make sure that I would come back to this blog page again sometime and keep on writing. For now this is a quick 5 min walk through of getting your hands dirty on the Singleton Pattern. As any ones first pattern Singleton always seems to be the easiest to adapt and ironically always the mistress of your pains; when you realize the act wasn't right in the first place.
More details on that later.

This post should help you to get your hands right on the Singleton Pattern and find the kind there off.

Like any other pattern Singleton also has an objective behind it. What is that?
*Motivation:*
A Singleton ensures that a class has only one instance, and provides a global point of access to that class.

*Benefits*
The very simple benefits of a singleton can be:

* Controlled access
* Permits a variable number of instances
* Reduced name space

*When to use:*
There must be exactly once instance of a class

*How to use: Walk Through*

1. Create a class

```
	public class SimplySingleton{}
```

2. Declare a member variable. This variable will be used for keeping the singleton instance.

It has to be private so that it is not accessible from anywhere else. It has to be static so that it holds only one instance in all entirety.

```
	private static SimplySingleton simplySingleton = null;
```

3. Declare a private constructor.

Creating a private constructor would mean no one else can instantiate this class.

```
	private SimplySingleton(){}
```

4. So now everything seems private how do we access it. Create a global access point.

```
	public static SimplySingleton getInstance(){}
```

How would I access it from outside SimplySingleton.getInstance();

This method should return a SimplySingleton instance.

So here comes the logic to create the one and only instance.

```
	// 4a. is the variable null?
	if(simplySingleton != null)
	return simplySingleton;
	// 4b. if not assign it an instance.
	else return simplySingleton = new SimplySingleton();
```

Following is the complete code listing for writing a Singleton.

```
	// Declaring the class
	public class SimplySingleton {
	// 1. a private and a static member variable
	private static SimplySingleton simplySingleton = null;
	// 2. a private constructor
	private SimplySingleton(){}
	// 3. a global access point

	public static SimplySingleton getInstance(){
		// 4a. is the variable null?
		if(simplySingleton != null)
		return simplySingleton;
		// 4b. if not assign it an instance.
		else return simplySingleton = new SimplySingleton();
		}

	}
	```

Following are some good resources for in depth peek into the Singleton Pattern.

*More Resources:*

[Singleton Pattern on wikipedia](http://en.wikipedia.org/wiki/Singleton_pattern)

[Implementing the Singleton Pattern in Java](href="http://radio.weblogs.com/0122027/stories/2003/10/20/implementingTheSingletonPatternInJava.html)

[OO Design](href="http://www.oodesign.com/singleton-pattern.html)

[SINGLETON PATTERN - 1. THREAD SAFETY](http://www.oaklib.org/docs/oak/singleton.html)
