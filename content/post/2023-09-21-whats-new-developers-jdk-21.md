---
title: "Whats New for developers in JDK 21"
date: 2023-09-21T09:28:11+02:00
tags: [java, jdk-21, release, openjdk]
image: /images/2023/09/21/java-21.jpeg
categories: ["Java"]
layout: post
type: post
---

>  *Orignally posted at* [Red Hat Developers](hhttps://developers.redhat.com/articles/2023/09/21/whats-new-developers-jdk-21)

In an exciting development for[ Java](https://developers.redhat.com/java) developers, this September 19th marked the release of JDK 21. This release contains many new capabilities that benefit the Java ecosystem, including virtual threads, record patterns, and sequenced collections. There are also some interesting features in the preview for JDK 21, such as string templates, scoped values, and structured concurrency. This article highlights six new features in this release.


## Virtual threads

Java's traditional threading model can quickly become an expensive operation if the application creates more threads than the operating system (OS) can handle. Also, in cases where the thread lifecycle is not long, the cost of creating a thread is high.

Enter[ virtual threads](https://openjdk.org/jeps/444), which solve this problem by mapping Java threads to carrier threads that manage (i.e., mount/unmount) thread operations to a carrier thread. In contrast, the carrier thread works with the OS thread. It is an abstraction that gives more flexibility and control for developers. See Figure 1.

![alt_text](https://developers.redhat.com/sites/default/files/styles/article_full_width_1440px_w/public/jdk-21-virtual-threads.png?itok=jo1UkiLr)


Figure 1: The virtual threading model in JDK 21.

The following is an example of virtual threads and a good contrast to OS/platform threads. The program uses the `ExecutorService` to create 10,000 tasks and waits for all of them to be completed. Behind the scenes, the JDK will run this on a limited number of carrier and OS threads, providing you with the durability to write concurrent code with ease.

```java
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10_000).forEach(i -> {
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        });
    });
}  // executor.close() is called implicitly, and waits


```

## Structured concurrency (Preview)

[Structured concurrency](https://openjdk.org/jeps/453) is closely tied to virtual threads, and it aims to eliminate common risks such as cancellation, shutdown, thread leaks, etc., by providing an API that enhances the developer experience. If a task splits into concurrent subtasks, then they should all return to the same place, i.e., the task's code block.

In Figure 2, `findUser` and `fetchOrder` both need to execute to get the data from different services and then use that data to compose results and send it back in a response to the consumer. Normally, these tasks could be done concurrently and could be error prone if `findUser` didn't return; `fetchOrder` would need to wait for it to complete, and then finally execute the Join operations.

![alt_text](https://developers.redhat.com/sites/default/files/styles/article_full_width_1440px_w/public/jdk-21-structured-concurrency.png?itok=Gls5cIv3)

Figure 2: Structured concurrency example.

Furthermore, the lifetime of the subtasks should not be more than the parent itself. Imagine a task operation that would compose results of multiple fast-running I/O operations concurrently if each operation is executed in a thread. The structured concurrency model brings thread programming closer to the ease of single-threaded code style by leveraging the virtual threads API and the `StructuredTaskScope`.

```java
Response handle() throws ExecutionException, InterruptedException {
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        Supplier<String>  user  = scope.fork(() -> findUser());
        Supplier<Integer> order = scope.fork(() -> fetchOrder());

        scope.join()            // Join both subtasks
             .throwIfFailed();  // ... and propagate errors

        // Here, both subtasks have succeeded, so compose their results
        return new Response(user.get(), order.get());
    }
}
```


## Sequenced collections

In[ JDK 21](https://openjdk.org/projects/jdk/21/), a new set of collection interfaces are introduced to enhance the experience of using collections (Figure 3). For example, if one needs to get a reverse order of elements from a collection, depending on which collection is in use, it can be tedious. There can be inconsistencies retrieving the encounter order depending on which collection is being used; for example, `SortedSet` implements one, but `HashSet` doesn't, making it cumbersome to achieve this on different data sets.


![alt_text](https://developers.redhat.com/sites/default/files/styles/article_full_width_1440px_w/public/image_0.png?itok=I6nIw--u)

Figure 3: Sequenced Collections.

To fix this, the[ SequencedCollection](https://openjdk.org/jeps/431) interface aids the encounter order by adding a reverse method as well as the ability to get the first and the last elements. Furthermore, there are also `SequencedMap` and `SequencedSet` interfaces. 

```java
interface SequencedCollection<E> extends Collection<E> {
    // new method
    SequencedCollection<E> reversed();
    // methods promoted from Deque
    void addFirst(E);
    void addLast(E);
    E getFirst();
    E getLast();
    E removeFirst();
    E removeLast();
}
```

So now, not only is it possible to get the encounter order, but you can also remove and add the first and last elements.


## Record patterns

Records were introduced as a preview in Java 14, which also gave us Java enums. `record` is another special type in Java, and its purpose is to ease the process of developing classes that act as data carriers only.

In JDK 21,[ record patterns](https://openjdk.org/jeps/440) and type patterns can be nested to enable a declarative and composable form of data navigation and processing.

```java
// To create a record:

Public record Todo(String title, boolean completed){}

// To create an Object:

Todo t = new Todo(“Learn Java 21”, false);
```

Before JDK 21, the entire record would need to be deconstructed to retrieve accessors.. However, now it is much more simplified to get the values. For example:

```java
static void printTodo(Object obj) {
    if (obj instanceof Todo(String title, boolean completed)) {
        	System.out.print(title);
System.out.print(completed);
    }
}
```

The other advantage of record patterns is also nested records and accessing them. An example from the JEP definition itself shows the ability to get to the `Point` values, which are part of `ColoredPoint`, which is nested in a `Rectangle`. This makes it way more useful than before, when all the records needed to be deconstructed every time. 


## String templates

[String templates](https://openjdk.org/jeps/430) are a preview feature in JDK 21. However, it attempts to bring more reliability and better experience to `String` manipulation to avoid common pitfalls that can sometimes lead to undesirable results, such as injections. Now you can write template expressions and render them out in a `String`. 

```java
// As of Java 21
String name = "Shaaf"
String greeting = "Hello \{name}";
System.out.println(greeting);
```

In this case, the second line is the expression, and upon invoking, it should render `Hello Shaaf`. Furthermore, in cases where there is a chance of illegal Strings for example, SQL statements or HTML that can cause security issues—the template rules only allow escaped quotes and no illegal entities in HTML documents.

## More JEPs in JDK 21

Other JEPs that I did not cover in this article but in another post
* JEP 439:[ Generational ZGC](https://openjdk.org/jeps/439)
* JEP 441:[ Pattern Matching for switch](https://openjdk.org/jeps/441)
* JEP 442:[ Foreign Function & Memory API (Third Preview)](https://openjdk.org/jeps/442)
* JEP 443:[ Unnamed Patterns and Variables (Preview)](https://openjdk.org/jeps/443)
* JEP 445:[ Unnamed Classes and Instance Main Methods (Preview)](https://openjdk.org/jeps/445)
* JEP 448:[ Vector API (Sixth Incubator)](https://openjdk.org/jeps/448)
* JEP 449:[ Deprecate the Windows 32-bit x86 Port for Removal](https://openjdk.org/jeps/449)
* JEP 451:[ Prepare to Disallow the Dynamic Loading of Agents](https://openjdk.org/jeps/451)
* JEP 452:[ Key Encapsulation Mechanism API](https://openjdk.org/jeps/452)



## **Get support for Java**

Support for OpenJDK and Eclipse Temurin is available to Red Hat customers through a subscription to[ Red Hat Runtimes](https://www.redhat.com/en/products/runtimes), Red Hat Enterprise Linux, and Red Hat OpenShift. Contact your local Red Hat representative or[ Red Hat sales](https://www.redhat.com/en/about/contact/sales) for more details. You can expect support for Java and other runtimes as described under the[ Red Hat Product Update and Support Lifecycle](https://access.redhat.com/support/policy/updates/jboss_notes/).


## **Resources**

* [Video: What is Eclipse Temurin?](https://www.youtube.com/watch?v=rKG6nvk9xlE) 	
* [Getting started with Eclipse Temurin](https://access.redhat.com/documentation/en-us/openjdk/17/html-single/getting_started_with_eclipse_temurin/index) 	
* [Red Hat joins the Eclipse Adoptium Working Group](https://www.redhat.com/en/blog/red-hat-joins-eclipse-adoptium-working-group) 	
* [Eclipse Adoptium achieves its first Java SE release](https://www.redhat.com/en/blog/eclipse-adoptium-achieves-its-first-java-se-release) 	
* [Red Hat Introduces Commercial Support for OpenJDK on Microsoft Windows](https://www.redhat.com/en/about/press-releases/red-hat-introduces-commercial-support-openjdk-microsoft-windows) 	
* [The history and future of OpenJDK](https://www.redhat.com/en/blog/history-and-future-openjdk) 	