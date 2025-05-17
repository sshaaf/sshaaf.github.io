---
title: "Java monitoring: Exploring Cryostat 2.4 features on OpenShift"
date: 2023-12-18T09:28:11+02:00
tags: [jfr, monitoring, java, jdk-21, release, openjdk]
image: /images/2023/12/18/java-monitoring-exploring-cryostat-24-features-openshift.jpeg
categories: ["Java"]
layout: post
type: post
---

>  *Orignally posted at* [Red Hat Developers](https://developers.redhat.com/articles/2023/12/18/java-monitoring-exploring-cryostat-24-features-openshift)


[Red Hat's latest build of Cryostat 2.4](https://developers.redhat.com/products/cryostat/overview), designed specifically for the [Red Hat OpenShift Container Platform](https://developers.redhat.com/products/openshift/overview), brings a wealth of features and enhancements that cater to various monitoring needs for [Java](https://developers.redhat.com/java) applications.

At its core, Cryostat 2.4 excels in comprehensive Java Flight Recorder (JFR) data management. Users can effortlessly start, stop, retrieve, archive, import, and export JFR data, all through an intuitive web console or an accessible HTTP API. This enhances the ease with which developers can handle JVM performance data. Moreover, Cryostat 2.4 provides flexibility in terms of data storage and analysis. Users can store and analyze JFR data directly on their Red Hat OpenShift or export it to external monitoring applications for a deeper dive into the data.


### **ARM (aarch64)**

A significant enhancement in Cryostat 2.4 is its support for Red Hat OpenShift Container Platform 4.11 and later versions, particularly for the ARM64 (aarch64) architecture. This broadens its applicability across various platforms, making it a versatile tool in diverse environments, e.g., edge deployments.


### **Smart triggering and HTTP API**

Another notable feature is the introduction of dynamic JFR recording with MBean custom triggers. The Cryostat agent is equipped with smart triggers that continuously monitor MBean counter values such as runtime, memory, thread, and operating system metrics. Users are able to set custom trigger conditions, thereby adding a layer of precision to JVM monitoring.

Further enhancing its functionality, Cryostat 2.4 introduces an improved HTTP API provided by the Cryostat agent. This serves as an alternative to an application’s JMX port, allowing users to fully utilize Cryostat's features without the need for JMX port exposure in target applications. This is particularly beneficial for enhancing security and simplifying configurations.


### **JAR distribution**

Cryostat 2.4 also offers flexibility in agent deployment. It provides two types of agent JAR file distributions—an all-in-one "shaded" JAR file that includes all dependencies, and a standard JAR file containing only the agent code. This choice caters to different user requirements and helps manage potential dependency conflicts more effectively.


### **Topology dashboard view**

Additionally, Cryostat 2.4 brings new features and fixes to enhance user experience. The Topology and Dashboard views in the Cryostat web console now display additional information about target JVMs, such as operating system name, memory statistics, class path, library paths, input arguments, and system properties. The introduction of a parameter to restart flight recordings offers more control over recording management, addressing a common user pain point.

Significant issues from previous versions have also been addressed. Automated rule-triggering issues in discovered JVM targets have been resolved, with Cryostat performing regular rechecks and reattempts at rule triggering. This ensures a more reliable connection with JVMs, improving consistency and predictability. The agent registration protocol has also seen improvements, resolving issues related to agent registration with the Cryostat server and ensuring a smoother, more reliable process.

Cryostat 2.4 is a testament to Red Hat's commitment to providing robust and innovative solutions for modern containerized applications. With its enhanced features, improved user experience, and greater flexibility, Cryostat 2.4 is poised to be a pivotal tool in JVM monitoring, offering a sophisticated and user-friendly approach to performance monitoring in containerized environments. 


### **How to use Cryostat for your Java workloads**

You can [install the Red Hat build of Cryostat](https://access.redhat.com/documentation/en-us/red_hat_build_of_cryostat/2/html/getting_started_with_cryostat/installing-cryostat-on-openshift-using-an-operator_cryostat) using our OpenShift operator, available in [Red Hat OpenShift](https://developers.redhat.com/products/openshift/overview)'s Operator Hub.
For non-production usage, you can also try our [Helm chart](https://developers.redhat.com/articles/2022/06/20/install-cryostat-new-helm-chart), included as part of OpenShift’s Helm chart repository.
You can also try Red Hat build of Cryostat [here](https://developers.redhat.com/products/cryostat/getting-started).


### **Get support for Java**

Support for Cryostat, OpenJDK, and Eclipse Temurin is available to Red Hat customers through a subscription to[ Red Hat Runtimes](https://www.redhat.com/en/products/runtimes), [Red Hat Enterprise Linux](https://developers.redhat.com/products/rhel/overview), and Red Hat OpenShift. Contact your local Red Hat representative or[ Red Hat sales](https://www.redhat.com/en/about/contact/sales) for more details. You can expect support for Java and other runtimes as described under the[ Red Hat Product Update and Support Lifecycle](https://access.redhat.com/support/policy/updates/jboss_notes/).


### **Resources**



* [Catch up with the latest on Java](https://developers.redhat.com/java)
* [Video: What is Eclipse Temurin?](https://www.youtube.com/watch?v=rKG6nvk9xlE)
* [Getting started with Eclipse Temurin](https://access.redhat.com/documentation/en-us/openjdk/17/html-single/getting_started_with_eclipse_temurin/index)
* [Red Hat joins the Eclipse Adoptium Working Group](https://www.redhat.com/en/blog/red-hat-joins-eclipse-adoptium-working-group)
* [Eclipse Adoptium achieves its first Java SE release](https://www.redhat.com/en/blog/eclipse-adoptium-achieves-its-first-java-se-release)
* [Red Hat Introduces Commercial Support for OpenJDK on Microsoft Windows](https://www.redhat.com/en/about/press-releases/red-hat-introduces-commercial-support-openjdk-microsoft-windows)
* [The history and future of OpenJDK](https://www.redhat.com/en/blog/history-and-future-openjdk)