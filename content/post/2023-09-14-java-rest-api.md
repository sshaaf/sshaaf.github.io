---
title: "Building a REST API in Java"
date: 2023-09-13 07:07:22 +02:00
image: /images/2023/09/14/quarkus-computer.jpeg
draft: true
categories: ["Java"]
---

Its 2023 and wondering about creating a REST API in Java. This tutorial will walk through some of the basics, how to build, document and test a REST API and I think the most awesome takeaway is *developing with [joy](https://quarkus.io/developer-joy/)*. So many frameworks claim bringing that joy. In this blog I will demonstrate the real Joy for all my Java developer friends. Atleast it should bring smiles to our faces for the ones who havent been touched by it yet ;)

Let's dig in!

>   "Have you heard about Developer Joy! he said.. "

### Objective
A Book Service
Build a backend service written in Java with [Quarkus](https://www.quarkus.io) that does the following. 
- The API is a Books API, uses a PG database in the backend to store the data. 
- This project uses Quarkus, develop from scratch with Dev services, Live coding, and continuous testing.
- It uses the Quarkus oidc extension to authorize against Keycloak (Next post)
- Deploy to Kubernetes/OpenShift
- An angular front-end for this service is also available [here](https://github.com/sshaaf/bookshelf-ui).
- API endpoints
  - GET -> getAll,
  - GET /{isbn} -> getOne,
  - DELETE /{isbn} -> remove,
  - POST -> create,
  - PUT /isbn -> update

**Prerequisites**: I am using [Eclipse Temurin](https://adoptium.net/temurin/releases/) Java version 17, Maven 3.9, and Docker. 
>  By the way if you havent tried [SDKMAN](https://sdkman.io/) you should, it just eases up installation of Java, Maven and some of the other tools. I use it alot for switching between my Java versions so I do not need to manage the PATH all the time. 


### Developer Joy Secret #1 - Quarkus CLI

```
~/demos 🐠  quarkus create app book-service && cd book-service
Looking for the newly published extensions in registry.quarkus.io
-----------

applying codestarts...
📚 java
🔨 maven
📦 quarkus
📝 config-properties
🔧 dockerfiles
🔧 maven-wrapper
🚀 resteasy-reactive-codestart

-----------
[SUCCESS] ✅  quarkus project has been successfully generated in:
--> /Users/.../demos/book-service
-----------
Navigate into this directory and get started: quarkus dev
```

```
Listening for transport dt_socket at address: 5005
__  ____  __  _____   ___  __ ____  ______ 
 --/ __ \/ / / / _ | / _ \/ //_/ / / / __/ 
 -/ /_/ / /_/ / __ |/ , _/ ,< / /_/ /\ \   
--\___\_\____/_/ |_/_/|_/_/|_|\____/___/   
2023-09-13 20:02:24,158 INFO  [io.quarkus] (Quarkus Main Thread) book-service 1.0.0-SNAPSHOT on JVM (powered by Quarkus 3.3.2) started in 1.657s. Listening on: http://localhost:8080

2023-09-13 20:02:24,164 INFO  [io.quarkus] (Quarkus Main Thread) Profile dev activated. Live Coding activated.
2023-09-13 20:02:24,165 INFO  [io.quarkus] (Quarkus Main Thread) Installed features: [cdi, resteasy-reactive, smallrye-context-propagation, vertx]
```



### Developer Joy Secret #2 - Dev Services a.k.a test containers integration



```
~/demos/book-service 🐠  quarkus ext add hibernate-orm-panache hibernate-validator jdbc-postgresql
Looking for the newly published extensions in registry.quarkus.io
[SUCCESS] ✅  Extension io.quarkus:quarkus-hibernate-orm-panache has been installed
[SUCCESS] ✅  Extension io.quarkus:quarkus-hibernate-validator has been installed
[SUCCESS] ✅  Extension io.quarkus:quarkus-jdbc-postgresql has been installed
```

```
2023-09-13 20:07:31,765 INFO  [io.qua.dat.dep.dev.DevServicesDatasourceProcessor] (build-5) Dev Services for default datasource (postgresql) started - container ID is 8f3f03aa7a8c
2023-09-13 20:07:31,768 INFO  [io.qua.hib.orm.dep.dev.HibernateOrmDevServicesProcessor] (build-42) Setting quarkus.hibernate-orm.database.generation=drop-and-create to initialize Dev Services managed database
__  ____  __  _____   ___  __ ____  ______ 
 --/ __ \/ / / / _ | / _ \/ //_/ / / / __/ 
 -/ /_/ / /_/ / __ |/ , _/ ,< / /_/ /\ \   
--\___\_\____/_/ |_/_/|_/_/|_|\____/___/   
2023-09-13 20:07:32,959 INFO  [io.quarkus] (Quarkus Main Thread) book-service 1.0.0-SNAPSHOT on JVM (powered by Quarkus 3.3.2) started in 4.841s. Listening on: http://localhost:8080

2023-09-13 20:07:32,962 INFO  [io.quarkus] (Quarkus Main Thread) Profile dev activated. Live Coding activated.
2023-09-13 20:07:32,963 INFO  [io.quarkus] (Quarkus Main Thread) Installed features: [agroal, cdi, hibernate-orm, hibernate-orm-panache, hibernate-validator, jdbc-postgresql, narayana-jta, resteasy-reactive, smallrye-context-propagation, vertx]
```

![alt_text](/images/2023/09/14/devservices.jpeg "Quarkus Dev Services - PG")


### Developer Joy Secret #3 - Continuous testing





### Developer Joy Secret #4 - Live coding



### Developer Joy Secret #5 - Kuberenetes deployments



### Developer Joy Secret #6 - Remote Dev