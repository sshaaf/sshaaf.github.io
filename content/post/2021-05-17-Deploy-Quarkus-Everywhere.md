---
title: Deploy Quarkus everywhere with Red Hat Enterprise Linux (RHEL)
tags: [quarkus, java, redhat, rhel, programming]
Category: Image Processing
date: 2021-05-07 07:07:22 +02:00
categories: ["Java"]
---

>  *Orignally posted at* [Red Hat Developers](https://developers.redhat.com/blog/2021/04/07/deploy-quarkus-everywhere-with-red-hat-enterprise-linux-rhel#)

Java is one of the most used languages out there and has been in the[ top three](https://www.tiobe.com/tiobe-index/?hid=B4E841AA3BF5CD6D546F03D321E49994&wordfence_lh=1) for the last two decades. Java powers millions of applications across verticals and platforms. Linux is widely deployed in data centers, Edge networks, and Cloud. Today we announce the availability of Quarkus for all our Red Hat Enterprise Linux (RHEL) customers. If you are running RHEL, you can now also run Red Hat Build of Quarkus (RHBQ). By doing this, we enable our customers, partners, and software vendors to use RHBQ in their applications with ease and furthermore enable them to deploy Quarkus for multiple use-cases for Java on Linux. If you are developing applications on a Kubernetes platform like Openshift, you can also use RHBQ with it, and this was[ announced](https://www.redhat.com/en/blog/introducing-quarkus-red-hat-openshift) last year. What is Quarkus and how can I develop and deploy it on RHEL? Learn more in this post.

 


### What is Red Hat Build of Quarkus (RHBQ)

If you are not familiar with [Quarkus](https://developers.redhat.com/products/quarkus/overview), "it is supersonic subatomic Java." Yes, Java is superfast! Java is light and straightforward with Quarkus. 

Quarkus is a Kubernetes-native[ Java framework](https://www.redhat.com/en/topics/cloud-native-apps/what-is-a-Java-framework) made for the JVM (Java Virtual Machine) and native compilation with GraalVM/Mandrel. Quarkus optimizes your Java code specifically for containers and enables it to become an effective platform for[ serverless](https://www.redhat.com/en/topics/cloud-native-apps/what-is-serverless) and[ cloud](https://www.redhat.com/en/topics/cloud) environments like Openshift. Quarkus is designed to work with popular Java standards, frameworks, and libraries like Eclipse MicroProfile and Spring and Apache Kafka, RESTEasy (JAX-RS), Hibernate ORM (JPA), Spring, Infinispan, Camel, and many more.


### How to get started with Quarkus on RHEL

There are multiple ways to start using quarkus on RHEL. All you need is to be able to get the artifacts from Red Hat’s maven repo. A list of different approaches is documented[ here](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/). 

For newbies, you can simply get started with the [project generator](https://code.quarkus.redhat.com) using a web browser or Maven plugin, as shown in Figure 1.  Once configured, you can download the zip file or copy the maven command to run on your machine. For more details on the different methods, you can check out the Quarkus documentation[ here](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/)<span style="text-decoration:underline;">.</span>



![alt_text](/images/image1.png "image_tooltip")


Figure 1. Quarkus project generator

Above, you will be able to see all the extensions that are supported in Tech Preview(TP) and also available for use. Quarkus has a vast ecosystem of extensions that help developers write applications such as Kafka, Hibernate Reactive, Panache, Spring, etc. 

 


### Example: Basic functions on RHEL

In our example today, we have already created a basic application that can run on a lightweight resource-efficient RHEL server, e.g. on the Edge. What does this application do? 



* Devices send data to an MQTT broker.
* Quarkus uses reactive messaging and channels to receive those messages, process them, and showcase them on a browser-based front-end. Data comes in real-time via a channel.
* The data is also stored in a Postgresql Database
* The front-end uses REST and Javascript.

This blog guides developers on how to implement the above scenario in terms of developing and deploying this application on RHEL using podman. Quarkus is able to detect the underlying container engine and build the containers for the application, as shown in Figure 2



![alt_text](/images/image2.png "image_tooltip")


Figure 2. High-level architecture diagram

In case you would like to follow along or try it out the source code for this application is located[ here](https://github.com/sshaaf/quarkus-edge-mqtt-demo). 


### Podman

Red Hat Enterprise Linux has a daemon less container engine.  What does this mean? RHEL uses Podman as the container engine. The Podman architecture by contrast allows you to run the containers under the user that is starting the container (fork/exec), and this user does not need any root privileges. Because Podman has a daemon less architecture, each user running Podman can only see and modify their own containers. There is no common daemon that the CLI tool communicates with. Learn more about Podman [here](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/8/html-single/building_running_and_managing_containers/index)

We will be using Podman throughout this example. 

 

Starting up the broker. For this demo, we are using the Mosquitto broker. Mosquitto is lightweight and is suitable for use on all devices from low power single board computers to full servers. We use it in this demo for a basic and simple MQTT broker. Let's start an instance of mosquitto using podman

 

```

podman run --name mosquitto \

--rm -p "9001:9001" -p "1883:1883" \

eclipse-mosquitto:1.6.2

```

 


### Building our application

Assuming you have the latest Red Hat build of[ ](https://access.redhat.com/articles/1299013)OpenJDK i.e. 11. 

You can check your version by initiating the following command on the terminal.

 
```
java -version

Output:

openjdk version "11.0.10" 2021-01-19

OpenJDK Runtime Environment 18.9 (build 11.0.10+9)

OpenJDK 64-Bit Server VM 18.9 (build 11.0.10+9, mixed mode, sharing)

```
 

So now we have Java and Mosquitto. Let's try to spin up our application. You can use any IDE (Integrated Development Environment) to develop with Quarkus. For most of them we have the “Quarkus Tools” extension which enables developers to create Quarkus with much more ease. Assuming you have an IDE of your choice. Let's start the Quarkus “dev mode”. 

To do that



* Open up a terminal (From your RHEL machine or any IDE)
* CD into our project directory i.e.[ quarkus-edge-mqtt-demo](https://github.com/sshaaf/quarkus-edge-mqtt-demo)
* Run command “mvn quarkus:dev”

 

The output should be similar, as shown in Figure3:


![alt_text](/images/image3.png "image_tooltip")


Figure 3. Quarkus Dev Mode

Open up a browser and navigate to[ http://localhost:8080](http://localhost:8080) 

You should be able to see the main page for our application reporting realtime data from our emulated device, as shown in Figure 4. The device in this case is an emulated one ESP8266-01 that throws Temperature and Heat measurements as a JSON format from the device into the MQTT broker. Then, that is picked up as a reactive channel and throws that data out after processing into the stream. The stream is read by the browser and displays the data in realtime. The emulated device can easily be changed to a real one, however the data thrown should be in the correct Json format.


![alt_text](/images/image4.png "image_tooltip")


Figure 4. Real-time Data from the device


### Developer Joy

By now, you have a running application on your RHEL machine in development mode. Quarkus is built for Java developers to enjoy developing applications with ease, comfort, and speed. It's a “cohesive platform for optimized developer joy”. So what benefits will developers gain from the development mode?



* Zero configuration, live code and reload in the blink of an eye, you don't need to restart the dev mode while developing. Quarkus understands!
* Based on standards, but not limited.
* Unified configuration
* Streamlined code for the 80% common usages, flexible for the 20%
* No hassle native executable generation

 

For example, if we change any of our Java files we don't need to reload the entire environment. 

If we hit the url[ http://localhost:8080/q/dev](http://localhost:8080/q/dev) you can also find an awesome Developer console available since[ RHBQ 1.11 release](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/1.11/html/release_notes_for_red_hat_build_of_quarkus_1.11/index)

You should see the following extensions, click on the SmallRye Reactive messaging “Channels”, as shown in Figure 5.


![alt_text](/images/image5.png "image_tooltip")


Figure 5. Quarkus DEV UI

Then you can see the Reactive streams that are being used for our Edge device, as shown in Figure 6.



![alt_text](/images/image6.png "image_tooltip")


Figure 6. Reactive Streams Channel

More details on development mode[ here](https://developers.redhat.com/blog/2021/02/11/enhancing-the-development-loop-with-quarkus-remote-development/)


### Using Podman to build application image

You can create a native binary for your platform by running the “-Pnative” directive with maven. 

However, assuming you might not have the entire compilation environment setup such as Mandrel or GraalVM installation. In that case, you can use your container runtime to build the native image as well. 

 

The simplest way to do this is by running the following command.

```
./mvnw package -Pnative -Dquarkus.native.container-build=true  -Dquarkus.native.container-runtime=podman
```

Quarkus will pick up the default container runtime(e.g. Podman) in our case.

You can also specify “-Dquarkus.native.container-runtime=podman” to explicitly select Podman. It takes a few minutes to build the image for optimizing the Quarkus application through dead code elements, class scanning, reflections, and build proxies. This will optimize not just for native images but also for JVM mode. So you will see fast startup times and a low memory footprint in both those cases, as shown in Figure 7


![alt_text](/images/image7.png "image_tooltip")


Figure 7. Quarkus Build Process

You can also limit the amount of memory used during native compilation by setting the quarkus.native.native-image-xmx configuration property. Setting low memory limits might increase the build time.  can also use podman to create a container image with our binary. 

Under src/main, different Dockerfiles are pre-generated by Quarkus for your application. In our example, we will use the native one, since we have already created a native binary.

 

Execute the following command in our project home directory

```
podman build -f src/main/docker/Dockerfile.native -t sshaaf/quarkus-edge-mqtt .
```
 

And finally, run the following command launches the container on your RHEL machine

podman run -i --rm -p 8080:8080 sshaaf/quarkus-edge-mqtt

Go back to[ http://localhost:8080](http://localhost:8080). Then, you should see our application running and showing incoming data from our device. 

 


### Summary

Quarkus is the Java framework for multiple use cases. Whether you are running on edge gateways, or creating serverless functions, or deploying on cloud environments like Kubernetes/OpenShift, Quarkus provides developer ease and joy, brings performance to Java applications for the cloud and its operational efficiency enables cost savings for running it everywhere.

In this blog, we learned about Quarkus on RHEL



* Using Quarkus(RHBQ) on RHEL
* Development mode
* Creating Java native executables with and without podman
* Creating images with Podman on RHEL

For more information and details, follow the resources below.



### Resources

Release [notes](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/1.11/html/release_notes_for_red_hat_build_of_quarkus_1.11/index) , Getting [started](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/1.11/html/getting_started_with_quarkus/index) , [documentation](https://access.redhat.com/documentation/en-us/red_hat_build_of_quarkus/)

Would like to learn more about Quarkus with Examples[ here](https://developers.redhat.com/courses/quarkus)

Books[ Practising Quarkus](https://developers.redhat.com/books/practising-quarkus),[ Understanding Quarkus](https://developers.redhat.com/books/understanding-quarkus)

[Quarkus Cheat Sheet](https://developers.redhat.com/cheat-sheets/quarkus-kubernetes-i),[ Quarkus reference card](https://dzone.com/refcardz/quarkus-1?chapter=1) 

Introducing Quarkus a next Generation Java[ framework](https://developers.redhat.com/blog/2019/03/07/quarkus-next-generation-kubernetes-native-java-framework/)
