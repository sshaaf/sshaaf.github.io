---
title: Creating and deploying a Java 8 runtime container image
tags: [microprofile, java, redhat, rhel, programming, docker, container]
Category: Image Processing
date: 2019-02-26 07:07:22 +02:00
categories: ["Java"]
---

>  *Orignally posted at* [Red Hat Developers](https://developers.redhat.com/blog/2019/02/26/create-java-8-runtime-container-image)

A Java runtime environment should be able to run compiled source code, whereas a development kit, for example, OpenJDK, would include all the libraries/binaries to compile and run the source code. Essentially the latter is a superset of the runtime environment. More details on OpenJDK support and lifecycle can be found [here](https://access.redhat.com/articles/1299013).

Red Hat ships and supports container images with OpenJDK for both Java 8 and 11. More details are [here](https://access.redhat.com/containers/#/search/openjdk). If you are using Red Hat Middleware, the s2i images shipped are also useful to deploy, for example, on Red Hat Openshift Container Platform.

Note that Red Hat only provides OpenJDK-based Java 8 and 11 images. With that said, there will certainly be situations where developers would like to create their own Java runtime images. For example, there could be reasons such as minimizing storage to run a runtime image. On the other hand, a lot of manual work around libraries such as Jolokio or Hawkular and even security parameters would need to be set up as well. If you'd prefer not to get into those details, I would recommend using the container images for OpenJDK shipped by Red Hat.

In this article we will:

    - Build an image with Docker as well as Buildah.
    - We will run that image with Docker as well as Podman on localhost.
    - We will push our image to Quay.
    - Finally, we will run our app by importing a stream into OpenShift.

This article was written for both OpenShift 3.11 and 4.0 beta. Let's jump right into it. 


## Setting up

To use our images and see how they work, we'll use a web app as part of our bundle. Recently Microprofile.io launched the [MicroProfile Starter beta](https://start.microprofile.io/), which helps you get started with MicroProfile by creating a downloadable package. Head out to [Microprofile.io](https://start.microprofile.io/) and get the package for MicroProfile with Thorntail V2.

![alt_text](/images/mp-starter-page.png "image_tooltip")

Getting the package for MicroProfile with Thorntail V2

Click the Download button to get the archive file.

On my Red Hat Enterprise Linux (RHEL) machine, I first create a temp directory, for example, demoapp, and unarchive the downloaded artifacts into it.

In my temp directory, I run:

```
$ mvn clean compile package
```

Now we should have a built demo app with a fat jar that we can call to run Thorntail.

Let’s copy the `target/demo-thorntail.jar` to the temp directory.

Here is the `Dockerfile` with comments on each layer. The source code of this file can also be found here on GitHub.

```
# A Java 8 runtime example
# The official Red Hat registry and the base image
FROM registry.access.redhat.com/rhel7-minimal
USER root
# Install Java runtime
RUN microdnf --enablerepo=rhel-7-server-rpms \
install java-1.8.0-openjdk --nodocs ;\
microdnf clean all
# Set the JAVA_HOME variable to make it clear where Java is located
ENV JAVA_HOME /etc/alternatives/jre
# Dir for my app
RUN mkdir -p /app
# Expose port to listen to
EXPOSE 8080
# Copy the MicroProfile starter app
COPY demo-thorntail.jar /app/
# Copy the script from the source; run-java.sh has specific parameters to run a Thorntail app from the command line in a container. More on the script can be found at https://github.com/sshaaf/rhel7-jre-image/blob/master/run-java.sh
COPY run-java.sh /app/
# Setting up permissions for the script to run
RUN chmod 755 /app/run-java.sh
# Finally, run the script
CMD [ "/app/run-java.sh" ]
```

Now that we have the Dockerfile details, let's go ahead and build the image.

One important point to note is that the OpenJDK Java runtime is packaged as "java-1.8.0-openjdk"; this does not include the compiler and other development libraries which are in the -devel package.

The above Dockerfile is built on RHEL, which means I do not need to register with subscription-manager, since the host already has the subscriptions attached.

Below you will find two ways to build this. If you are running RHEL like I am, you can choose any of the two binaries to deploy from. Both of them should be in rhel7-server-extras-rpms.

You can enable the extras repo like this:

```
# subscription-manager repos --enable rhel-7-server-extras-rpms 
```

## Build and run images locally

Building the image with docker:

```
$ docker build -t quay.io/sshaaf/rhel7-jre8-mpdemo:latest .
```

Running the image with docker and pointing localhost:8080 to the container port 8080:

```
$ docker run -d -t -p 8080:8080 -i quay.io/sshaaf/rhel7-jre8-mpdemo:latest
```

We can also use the buildah command, which helps to create container images from a working container, from a Dockerfile or from scratch. The resulting images are OCI-compliant, so they will work on any runtimes that meet the OCI Runtime Specification (such as Docker and CRI-O).

Building with buildah:

```
$ buildah bud -t rhel7-jre8-mpdemo .
```

Creating a container with buildah:

```
$ buildah from rhel7-jre8-mpdemo
```

Now we can also run the container with Podman, which complements Buildah and Skopeo by offering an experience similar to the Docker command line: allowing users to run standalone (non-orchestrated) containers. And Podman doesn’t require a daemon to run containers and pods. Podman is also part of the extras channel and the following command should run the container.

```
$ podman run -d -t -p 8080:8080 -i quay.io/sshaaf/rhel7-jre8-mpdemo:latest
```

More details on Podman can be found in Containers without daemons: Podman and Buildah available in RHEL 7.6 and RHEL 8 Beta and Podman and Buildah for Docker users.

Now that we have an image, we would also like to deploy it to OpenShift and test our app. For that, we need the oc client libraries. I have my own cluster setup; you could choose to use Red Hat Container Development Kit (CDK)/minishift, Red Hat OpenShift Online, or your own cluster. The procedure should be the same. 

## Deploying to OpenShift

To deploy to OpenShift, we need to have the following few constructs:

    An image stream for our newly created container image
    Deployment configuration for OpenShift
    Service and routing configurations

### Image stream

To create the image stream, my OpenShift cluster should be able to pull the container image from somewhere. Up until now, the image has been residing on my own machine. Let's push it to Quay. The Red Hat Quay container and application registry provides secure storage, distribution, and deployment of containers on any infrastructure. It is available as a standalone component or in conjunction with OpenShift.

First I need to log in to Quay, which I can do as follows:

```
$ docker login -u="sshaaf" -p="XXXX" quay.io

```
And then we push our newly created image to Quay:

```
$ docker push quay.io/sshaaf/rhel7-jre8-mpdemo

```
Let's take a look at the constructs before we deploy. For the anxious, you can skip the details on the deployment template and head down to project creation.

Now that we have the image, we define our stream:

```
- apiVersion: v1
kind: ImageStream
metadata:
name: rhel7-jre8-mpdemo
spec:
dockerImageRepository: quay.io/sshaaf/rhel7-jre8-mpdemo

```
Again, you can see above we point directly to our image repository at Quay.io.
Deployment config

Next up is the deployment config, which sets up our pods and triggers and points to our newly created stream, etc.

If you are new to containers and OpenShift deployments, you might want to look at this useful [ebook](https://www.openshift.com/deploying-to-openshift/).

```
- apiVersion: v1
kind: DeploymentConfig
metadata:
name: rhel7-jre8-mpdemo
spec:
template:
metadata:
labels:
name: rhel7-jre8-mpdemo
spec:
containers:
- image: quay.io/sshaaf/rhel7-jre8-mpdemo:latest
name: rhel7-jre8-mpdemo
ports:
- containerPort: 8080
protocol: TCP
replicas: 1
triggers:
- type: ConfigChange
- imageChangeParams:
automatic: true
containerNames:
- rhel7-jre8-mpdemo
from:
kind: ImageStreamTag
name: rhel7-jre8-mpdemo:latest
type: ImageChange
```

### The service

Now that have our deployment, we also want to define a service that will ensure internal load balancing, IP addresses for the pods, etc. A service is important if we want our newly created app to be finally exposed to outside traffic.

```
- apiVersion: v1
kind: Service
metadata:
name: rhel7-jre8-mpdemo
spec:
ports:
- name: 8080-tcp
port: 8080
protocol: TCP
targetPort: 8080
selector:
deploymentconfig: rhel7-jre8-mpdemo
```

The route

And the final piece of our deployment is the route. It's time we expose or app to the outside world with the route. We can define which internal service this route points to and which port to target. OpenShift will give it a friendly URL that we will be able to point to and see our resulting MicroProfile app running on our newly created Java 8 runtime–based deployment.

```
- apiVersion: v1
kind: Route
metadata:
name: rhel7-jre8-mpdemo
spec:
port:
targetPort: 8080-tcp
to:
kind: Service
name: rhel7-jre8-mpdemo
weight: 100
```

The complete template for the above can be found [here on GitHub](https://raw.githubusercontent.com/sshaaf/rhel7-jre-image/master/deployment.yaml).

Let’s also create a project in OpenShift like this:

```
$ oc new-project jredemos

```
And now we process the template and get our demo with the Java 8 runtime on OpenShift. To do that, run the following command:

```
$ oc process -f deployment.yaml  | oc create -f -

```
This will create the entire deployment, and you should be able to see something like this:

Results of creating the entire deployment

Now run the following command:

```
$ oc get routes

```
This will show the routes, as follows:

### The routes

Let's copy the route into our browser and we should see the web app deployed running on RHEL 7 with the Java 8 runtime. (The address below is specific to test the cluster only and will be different per cluster.)

http://rhel7-jre8-mpdemo-jredemos.apps.cluster-1fda.1fda.openshiftworkshop.com/


## Summary

We have successfully built and created a Java 8 runtime container image with Docker or Buildah. Be aware of the following:

+ It's important to note that this image is to show how this can be done; it doesn't include things like Jolokio or Hawkular, which could be necessary for deployments.
+ Moreover, it does not take into consideration parameters required for running Java apps in containers, which are very well explained in this [article](https://developers.redhat.com/blog/2017/03/14/java-inside-docker/) by Rafael Benevides.
+ Furthermore, when deploying your own container images, always remember to check the support and lifecycle policy, if you are running Red Hat’s build of OpenJDK.

We then deployed this to OpenShift with our basic MicroProfile demo app from the [MicroProfile Starter beta](https://start.microprofile.io/).

If you are looking into creating a more comprehensive demo application, the following are great resources:

+ [Deploying MicroProfile apps on Microsoft Azure using the Azure Open Service Broker](https://developers.redhat.com/blog/2018/10/17/microprofile-apps-azure-open-service-broker/)
+ The MicroProfile ebook [here](http://bit.ly/MP-ebook)

The entire resources for this article can be found here.