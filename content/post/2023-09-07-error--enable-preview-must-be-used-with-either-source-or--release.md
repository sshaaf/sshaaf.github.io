---
title: "error: --enable-preview must be used with either -source or --release"
tags: [java, jdk21]
date: 2023-09-07T15:00:48+02:00
---

The JDK 21 release is well underway likely to drop around September 19th, and its not GA yet. further more it provides preview features. 

It was time for downloading one of the releases and giving it a try. Well I have given it a try some weeks ago so I already had it installed. 
e.g. 

```
openjdk version "21-ea" 2023-09-19
OpenJDK Runtime Environment (build 21-ea+26-2328)
OpenJDK 64-Bit Server VM (build 21-ea+26-2328, mixed mode, sharing)
```

The fun thing though is that there are couple of very cool features that are still in preview. e.g. I tried to use the StringTemplates mentioned in the [InfoQ blog](https://www.infoq.com/news/2023/04/java-gets-a-boost-with-string/)


```
~/git/java-examples 🐠  javac StringTemplates.java                                               14:50
StringTemplates.java:6: error: string templates are a preview feature and are disabled by default.
    public static String html = STR."""
                                    ^
  (use --enable-preview to enable string templates)
1 error
```

To compile with features enabled. use the following example command 

```
javac StringTemplates.java --enable-preview --release 21

```

And finally to run you would also want to enable the preview

```
~/git/java-examples 🐠  java --enable-preview StringTemplates                                    14:56
<html>
  <head>
    <title>My Web Page</title>
  </head>
  <body>
    <p>Hello, world</p>
  </body>
</html>

```

List of included JEPs in Java 21:

| JEP         | Title     |
|---|-------------------------------------------------------------------------------------|
430 | [String Templates (Preview)](https://openjdk.org/jeps/430)                          |
431 | [Sequenced Collections](https://openjdk.org/jeps/431)                               |
439 | [Generational ZGC](https://openjdk.org/jeps/439)                                    |
440 | [Record Patterns](https://openjdk.org/jeps/440)                                     |
441 | [Pattern Matching for switch](https://openjdk.org/jeps/441)                         |
442 | [Foreign Function & Memory API (Third Preview)](https://openjdk.org/jeps/442)       |
443 | [Unnamed Patterns and Variables (Preview)](https://openjdk.org/jeps/443)            |
444 | [Virtual Threads](https://openjdk.org/jeps/444)                                     |
445 | [Unnamed Classes and Instance Main Methods (Preview)](https://openjdk.org/jeps/445) |
446 | [Scoped Values (Preview)](https://openjdk.org/jeps/446)                             |
448 | [Vector API (Sixth Incubator)](https://openjdk.org/jeps/448)                        |
449 | [Deprecate the Windows 32-bit x86 Port for Removal](https://openjdk.org/jeps/449)   |
451 | [Prepare to Disallow the Dynamic Loading of Agents](https://openjdk.org/jeps/451)   |
452 | [Key Encapsulation Mechanism API](https://openjdk.org/jeps/452)                     |
453 | [Structured Concurrency (Preview)](https://openjdk.org/jeps453)                     |

