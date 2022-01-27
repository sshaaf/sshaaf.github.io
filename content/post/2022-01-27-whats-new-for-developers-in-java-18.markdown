---
title: What's new for developers in Java 18
tags: [java, redhat, programming]
Category: Java
date: 2022-01-27 07:07:22 +02:00
---

>  *Orignally posted at* [Red Hat Developers](https://developers.redhat.com/articles/2022/01/27/whats-new-developers-java-18#)



In exciting news for [Java](https://developers.redhat.com/topics/enterprise-java) developers, Java 18 forked off from the main line [at the end of last year](https://www.infoq.com/news/2021/12/java-news-roundup-dec06-2021/) and has entered [Rampdown Phase Two](https://openjdk.java.net/projects/jdk/18/). This article highlights some of the features that developers can look for in the upcoming Java 18 release, including the new simple web server module, a more sophisticated way to annotate your Javadocs, and the `–finalization=disabled` option, which lets you test how a Java application will behave when finalization is removed in a future release. See the end of the article for where to download Java 18 in early access builds.


## **Java's new simple web server**

Java 18 will provide a minimally functional web server in the `jdk.httpserver` module. It has an API for access, as well as a binary in the `bin` directory in case you want to run the server from the command line.

The command to run the web server can be as simple as:


```
$ jwebserver -b 0.0.0.0 -p 8000
```

Note:** For more command-line options and details about the `jdk.httpserver` module, see the [JEP 408 documentation](https://openjdk.java.net/jeps/408).

If you are wondering whether you can implement a full-blown production web server using the simple web server APIs, the answer is no. The web server is definitely not intended for that use. For one thing, it communicates over HTTP/1.1 and doesn't support PUT requests, so it doesn't support dynamic content. The web server is recommended for prototyping, testing, and debugging. An example code snippet with comments follows:


```
import java.net.InetSocketAddress;
import java.nio.file.Path;
import com.sun.net.httpserver.SimpleFileServer;
import static com.sun.net.httpserver.SimpleFileServer.OutputLevel;

public class App {
public static void main( String[] args ){
    // Create a simple file server, given the socket address, path and output level
    var server = SimpleFileServer.createFileServer(new InetSocketAddress(8000),             Path.of("/home/java"), OutputLevel.VERBOSE);

    // Starting the server
    server.start();

    // A friendly message to get started.
    System.out.println( "We are getting started.. Hello World!" );
  }
}
```

## **Code snippets in Java API documentation**

Prior to Java 18, developers mostly inserted code samples in Javadoc comments using the `@code` annotation. That technique is somewhat limited and requires workarounds. For instance, it has always been difficult to validate what's inside the code fragment, implement syntax highlighting, and insert links or escape characters.

As a new approach, JEP 413 proposes using the `@snippet` tag. As noted in the JEP, the tag "can be used to declare both _inline snippets_, where the code fragment is included within the tag itself, and _external snippets_, where the code fragment is read from a separate source file."

Here is an example of an inline snippet:


```
/**
* The following code shows how to use {@code Optional.isPresent}:
* {@snippet :
* if (v.isPresent()) {
*     System.out.println("v: " + v.get());
* }
* }
*/
```


The code lies between curly braces, where the opening brace is followed by the `@snippet` tag. The Javadoc utility now also includes options to specify links, highlight code, and more. See [JEP 413](https://openjdk.java.net/jeps/413) for more details.


## **UTF-8 character set by default**

In prior releases, the default character set was determined when the Java runtime started, and depended on the user's locale and default encoding. Thus, on Windows the charset was `windows-1252`, whereas on macOS it was UTF-8 except in the POSIX C locale. With Java 18, UTF-8 will be the default for all operating systems.

You can change the default charset by setting the `file.encoding` to `COMPAT`; for instance, by running `java -Dfile.encoding=COMPAT`. This setting reverts to the algorithm in Java 17.


## **Prepare now for the removal of finalize()**

If you have developed Java applications, you are probably familiar with the `finalize()` method. Since Java 9, the recommendation has been to not use `finalize()`, but instead to use a _try-with-resources_ statement or the new Cleaner APIs. JEP 421 helps developers prepare for the eventual removal of finalization. You can run an application with the `–finalization=disabled` option to see how it will behave without the `finalize()` method. It's great to see this evolution. As a developer, it is also an opportunity to take a closer look at your application's behavior.


**Note: **A recent [Inside Java podcast episode](https://inside.java/2022/01/12/podcast-021/) discusses issues with finalization and what to expect in Java 18. See the documentation for [JEP 421](https://openjdk.java.net/jeps/421) for more details.


## **Preview features in Java 18**

Some of the features that were included in the development phase of Java 18 are still in preview. These include the Vector API ([JEP 417](https://openjdk.java.net/jeps/417)), which Gunnar Morling discusses in this [DevNation Tech Talk](https://developers.redhat.com/devnation/tech-talks/java17-apis). The foreign function and memory API ([JEP 419](https://openjdk.java.net/jeps/419)) and pattern matching for `switch` ([JEP 420](https://openjdk.java.net/jeps/420)) also remain in preview.


## **Where to download Java 18**

To give Java 18 a try, you can download the early access [Eclipse Temurin builds](https://adoptium.net/archive.html?variant=openjdk18&jvmVariant=hotspot) from Eclipse Adoptium. Temurin is the [name of the OpenJDK distribution](https://adoptium.net/faq.html#temurinName) from Adoptium.

If you are using a current version of Java and want to compare the features with Java 18, I would also highly recommend the [Java Almanac](https://javaalmanac.io/). It contains a [page listing all the new features and changes in Java 18](https://javaalmanac.io/jdk/18/).


## **Conclusion**

This article was a quick look at some of the highlights of Java 18. Keep an eye on the [Red Hat Developer OpenJDK page](https://developers.redhat.com/products/openjdk) for more Java 18 updates. You can also get started using the [Red Hat build of OpenJDK](https://developers.redhat.com/products/openjdk/getting-started).

