---
title: "Ensure Secure and Up-to-date Projects with the Outdated Maven Plugin"
date: 2024-07-14
image: "/images/2024/07/14/serverfarm-vaporware.jpeg"
tags: ["java", "maven"]
categories: ["Java"]
---

It's not an early Sunday morning. Sipping some Coffee and going through my feed and I find this gem that [@Markus Eisele](https://mastodon.online/@myfear/112783939377718420) just posted. 
Well at first I saw the post as "Outdated Maven Plugin", and I am like what does that mean? Anyways going into the git repo I see its a new project by [Giovanni van der Schelde](https://giovds.com/). 

> Stay up-to-date and secure with The Outdated Maven Plugin!
The Outdated Maven Plugin is a tool designed to help developers identify outdated dependencies in their Maven projects.
By scanning the dependencies of your project, this plugin determines if they are no longer actively maintained
based on a user-defined threshold of inactivity in years. This ensures that your project remains up-to-date with the
latest and most secure versions of its dependencies.


This really solves a problem at large. There are many environments where old binaries are being used. On top of that if users can specify a check on the threshold to keep up to the pace of binaries is a great aid. A quick search online renders results on how to find ununsed libraries via the [maven dependency plugin](https://www.baeldung.com/maven-unused-dependencies). Its easy to loose track of dependencies being used. Its also a great aid. 

This plugin however is checking on the updates and giving developers and users data that there might be something important to look into, especially if the libraries are old or might have potential security risks. 

To start I just drag in the following plugin into my project pom.xml. Well its not really my project I just went ahead and cloned the [Apache Struts examples repo](https://github.com/apache/struts-examples/tree/master) from github and tried it out. Sorry Apache Struts but its one that comes to mind when I think of programming web systems a decade and more .. ago.. 

```
        <plugin>
            <groupId>com.giovds</groupId>
            <artifactId>outdated-maven-plugin</artifactId>
            <version>1.0.0</version>
            <configuration>
                <!-- The maximum amount of inactive years allowed -->
                <years>1</years>
                <!-- Whether to fail the build if an outdated dependency is found -->
                <shouldFailBuild>false</shouldFailBuild>
            </configuration>
            <executions>
                <execution>
                    <id>outdated-check</id>
                    <goals>
                        <goal>check</goal>
                    </goals>
                </execution>
            </executions>
        </plugin>
```
- Notice that in the above plugin `<configuration>` there are two parameters. 
- `<years>`: any library that is older then 1 year
- `<shouldFailBuild>`: we dont want the build to fail so its set to false.

Then to run the this over my project I run the following command.
```maven
mvn com.giovds:outdated-maven-plugin:check
```

So here is an interesing output. The module [rest-angular](https://github.com/apache/struts-examples/tree/master/rest-angular) has outdated dependencies according to the above criteria. (1 years)
```
[INFO] -------------------< org.apache.struts:rest-angular >-------------------
[INFO] Building REST Plugin based application with AngularJS 1.1.0      [33/47]
[INFO]   from rest-angular/pom.xml
[INFO] --------------------------------[ war ]---------------------------------
[INFO] 
[INFO] --- outdated:1.0.0:check (default-cli) @ rest-angular ---
[WARNING] Dependency 'org.hamcrest:hamcrest-all:1.3' has not received an update since version '1.3' was last uploaded '2012-07-09'.
[WARNING] Dependency 'org.hibernate.validator:hibernate-validator:6.2.3.Final' has not received an update since version '6.2.3.Final' was last uploaded '2022-03-03'.
[WARNING] Dependency 'org.glassfish:javax.el:3.0.1-b12' has not received an update since version '3.0.1-b12' was last uploaded '2020-10-12'.
[WARNING] Dependency 'com.fasterxml.jackson.core:jackson-core:2.14.1' has not received an update since version '2.14.1' was last uploaded '2022-11-22'.
[WARNING] Dependency 'com.fasterxml.jackson.core:jackson-annotations:2.14.1' has not received an update since version '2.14.1' was last uploaded '2022-11-22'.
[WARNING] Dependency 'com.fasterxml.jackson.core:jackson-databind:2.14.1' has not received an update since version '2.14.1' was last uploaded '2022-11-22'.
[WARNING] Dependency 'com.fasterxml.jackson.dataformat:jackson-dataformat-xml:2.14.1' has not received an update since version '2.14.1' was last uploaded '2022-11-22'.
[WARNING] Dependency 'junit:junit:4.13.2' has not received an update since version '4.13.2' was last uploaded '2021-02-13'.
[WARNING] Dependency 'com.jayway.jsonpath:json-path:2.7.0' has not received an update since version '2.7.0' was last uploaded '2022-01-30'.
[WARNING] Dependency 'javax.servlet:javax.servlet-api:4.0.1' has not received an update since version '4.0.1' was last uploaded '2018-04-20'.
[WARNING] Dependency 'javax.servlet:jsp-api:2.0' has not received an update since version '2.0' was last uploaded '2005-11-08'.
``` 

The output is nice and clean.
`Dependency` name, and `version`, and the last uploaded to maven repo. 

I did run into an issue though. Where I am running Java 17. But the plugin is complied with the latest Java LTS version 21. 

```
    Execution default-cli of goal com.giovds:outdated-maven-plugin:1.0.0:check failed: 
    Unable to load the mojo 'check' in the plugin 'com.giovds:outdated-maven-plugin:1.0.
    0' due to an API incompatibility: org.codehaus.plexus.component.repository.exception.
    ComponentLookupException: com/giovds/OutdatedMavenPluginMojo has been compiled by a 
    more recent version of the Java Runtime (class file version 65.0), this version of
    the Java Runtime only recognizes class file versions up to 61.0
``` 


I do think that there will be projects out there using versions 17 or earlier. [State of the Java ecosystem report by New Relic](https://newrelic.com/sites/default/files/2024-05/new-relic-state-of-the-java-ecosystem-2024-05-29.pdf) also points out some of the versions in use. And I do think alot of older Java environments are the kind of environments where a tool like this will be be super useful to help aid users further. 