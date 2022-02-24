---
title: SQL cache stores and more in Data Grid 8.3
tags: [java, cache, redhat, programming, infinispan]
Category: Java
date: 2022-02-24 07:07:22 +02:00
---

>  *Orignally posted at* [Red Hat Developers](https://developers.redhat.com/articles/2022/02/24/sql-cache-stores-and-more-data-grid-83)

[Red Hat Data Grid](https://developers.redhat.com/products/datagrid/overview) is a distributed, cloud-based datastore offering very fast response times as an in-memory database. The latest version, Data Grid 8.3, features cross-site replication with more observability and two new types of SQL cache store for scaling applications with large datasets. This version also brings improved security, support for Helm charts, and a better command-line interface (CLI).

This article is an overview of new features and enhancements in this latest version of Red Hat Data Grid.

## **Cross-site replication with more observability**

With the latest Data Grid release, you can track cross-site replication operations for each of the backup locations and their caches, including response times and the number of RELAY messages exchanged, as shown in Figure 1.

![alt_text](https://developers.redhat.com/sites/default/files/repl.png "image_tooltip")


Figure 1. Cross-site replication involves messages at many different levels.

We have also enabled access to the data via the CLI, the REST API, and Java Management Extensions (JMX) to offer a better user experience to cluster operators. Cross-site replication is also more transparent and observable due to dedicated, operator-managed pods for routing cross-site replication requests.

Data Grid operators can also configure the number of relay nodes for cross-site replication. This flexibility enhances the cache's scalability and performance over multiple sites.

Finally, security is of paramount importance for a cross-site cluster, so we have enabled TLS security for router-based cross-site replication. (Scroll down for more about security enhancements in a later section.)


## **Scaling with SQL cache stores**

What do you do if you have a lot of data in a database and want to load the data into the cache? Database schemas can be complex and users might want to define how that data is queried through operations such as SELECT, INSERT, and so on. Perhaps you would also like to support write-through and write-back operations. All of this makes for a complex scenario.

In this release, we have added two types of SQL cache store:

* Table cache store: Loads all data from a single table. Only the table name is required.
* Query cache store: Loads data based on SQL queries.

Useful things you can do with the new SQL cache stores include the following:



* Pre-load data from an existing database.
* Expose cache data with a user-defined schema.
* Allow read and write operations.
* Configure the cache store as read-only, and act as a cache loader.
* Configure the cache store to load values on startup.
* Use the cache store with composite keys and values through the [protocol buffers (protobuf) schema](https://developers.google.com/protocol-buffers).
* With the query cache store, use arbitrary select, select all, delete, delete all, and upsert operations.

To set up a cache store, you simply need to drop the database drivers into the server, which can be done with the [Operator](https://developers.redhat.com/articles/2022/02/24/sql-cache-stores-and-more-data-grid-83) custom resource (CR) on [Red Hat OpenShift](https://developers.redhat.com/openshift). After that, users should be able to create SQL cache stores via YAML, JSON, or XML—also a new configuration feature. An [example using Infinispan and the Quarkus Java framework](https://github.com/redhat-mw-demos/infinispan-sqlstore-demo) is available on GitHub.


## **More security enhancements**

Data Grid now provides full support for TLS version 1.3 with OpenSSL native acceleration. We have also increased the flexibility and convenience of security in Data Grid 8.3.


### **Multiple realms**

You can combine multiple security realms into a single realm. When authenticating users, Data Grid Server checks each security realm in turn until it finds one that can perform the authentication.

The following example security realm includes an LDAP realm and a property realm, along with the `distributed-realm` element:


```
<security-realms>
   <security-realm name="my-distributed-realm">
      <ldap-realm>
         <!-- LDAP realm configuration. -->
      </ldap-realm>
      <properties-realm>
         <!-- Property realm configuration. -->
      </properties-realm>
      <distributed-realm/>
   </security-realm>
</security-realms>
```

### **Multiple endpoints**

Users can now also configure multiple endpoints and define separate security realms for them. This enhancement enables more flexible and secure use.

The following example contains two different endpoint configurations. One endpoint binds to a `public` socket, uses an `application` security realm, and disables administrative features. Another endpoint binds to a `private` socket, uses a `management` security realm, and enables administrative features:


```
<endpoints>
  <endpoint socket-binding="public"
            security-realm="application"
            admin="false">
    <hotrod-connector/>
    <rest-connector/>
  </endpoint>
  <endpoint socket-binding="private"
            security-realm="management">
    <hotrod-connector/>
    <rest-connector/>
  </endpoint>
</endpoints>
```

### **PEM files**

Users can now add PEM files directly to their Data Grid Server configuration and use them as trust stores and keystores in a TLS server identity.


    Note: See the [Data Grid Security Guide](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/html-single/data_grid_security_guide/) and [Distributed security realms](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/html-single/data_grid_server_guide#distributed-security-realms_security-realms) to learn more about new security features in Data Grid 8.3.

## **Deploy Data Grid with Helm charts**

Developers who use [Helm charts](https://helm.sh/) for application deployment can now use this convenient mechanism to install Data Grid. You can use charts to deploy Data Grid instances, configure clusters, add authentication and authorization, add network access via routes and node ports, enable load balancers, and more, using the Data Grid portal (Figure 2) or the CLI.


![alt_text](https://developers.redhat.com/sites/default/files/styles/article_full_width_1440px_w/public/helm_0.png?itok=1XGArnkV "image_tooltip")


Figure 2. Helm charts can be invoked through the Data Grid graphical interface.


    **Note:** Using Helm charts is intended for sites where the Data Grid Operator is not available and operators must configure, deploy, and manage the cluster manually.

## **CLI improvements**

Data Grid 8.3 has a few updates for developers who prefer working on the command line. For one, you can enable and disable rebalancing of the cluster, track and extract more details about cross-site replication relay nodes, and manage cache availability. Additionally, if you use the general `oc` OpenShift command, you can now also [install](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.3/guide/d510c8ad-e097-4a3e-af55-e1d7967ecac3) the Infinispan extension and use it with `oc`, as shown in Figure 3.


![alt_text](https://developers.redhat.com/sites/default/files/styles/article_full_width_1440px_w/public/control.png?itok=heoMJq24 "image_tooltip")


Figure 3. You can control a Data Grid cluster from the command line.


## **Usability improvements**

We've made a few more improvements to increase the usability of Data Grid in this release:



* Data Grid 8.3 has full support for [Java 17](https://developers.redhat.com/articles/2021/12/14/explore-java-17-language-features-quarkus) for embedded and remote caches.
* You can automatically migrate any file-store configuration during the upgrade to Data Grid 8.3.
* You can now delete entries with the [Ickle programming language](https://access.redhat.com/documentation/ru-ru/red_hat_data_grid/7.1/html/developer_guide/building_ickle_query):
* <code>query.<strong>create</strong>("<strong>DELETE</strong> FROM books WHERE page_count > 500").executeStatement();</code>
* Copy snippet
* Hot Rod migration is simpler when upgrading clusters of server nodes between versions and handles configuration changes transparently.


## <strong>Get started with Data Grid 8.3</strong>

Ready to dive in and try out Data Grid 8.3? These resources will get you started:



* Zip distributions are available through the [Certified Service Provider (CSP) program](https://access.redhat.com/jbossnetwork/restricted/listSoftware.html?product=data.grid&downloadType=distributions).
* Container distributions and Operators are available in the [Red Hat Container Catalog](https://access.redhat.com/containers/#/product/JbossDataGrid).
* Product documentation is available on the [Red Hat customer portal](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.0/), including [a migration guide](https://access.redhat.com/documentation/en-us/red_hat_data_grid/8.0/html/data_grid_migration_guide/) to help you migrate your existing Data Grid deployments to 8.0.

Visit the [Red Hat Data Grid](https://developers.redhat.com/products/datagrid) product page to learn more about this technology.


## **Recent Articles**

* **[Inspecting containerized Python applications in a cluster](https://developers.redhat.com/articles/2022/02/24/inspecting-containerized-python-applications-cluster)**
* **[SQL cache stores and more in Data Grid 8.3](https://developers.redhat.com/articles/2022/02/24/sql-cache-stores-and-more-data-grid-83)**
* **[Debug .NET applications running in local containers with VS Code](https://developers.redhat.com/articles/2022/02/22/debug-net-applications-running-local-containers-vs-code)**
* **[Quality testing the Linux kernel](https://developers.redhat.com/articles/2022/02/17/quality-testing-linux-kernel)**
* **[Code specialization for the MIR lightweight JIT compiler](https://developers.redhat.com/articles/2022/02/16/code-specialization-mir-lightweight-jit-compiler)**


## **Related Content**
* **[Using Red Hat Data Grid to power a multi-cloud real-time game](https://developers.redhat.com/blog/2018/06/26/data-grid-multi-cloud-real-time-game)**
* **[Implementing a Log Collector using Red Hat JBoss Fuse and Red Hat JBoss Data Grid](https://developers.redhat.com/blog/2017/05/30/implementing-a-log-collector-using-red-hat-jboss-fuse-and-red-hat-jboss-data-grid)**
* **[Develop and test a Quarkus client on Red Hat CodeReady Containers with Red Hat Data Grid 8.0](https://developers.redhat.com/blog/2020/06/19/develop-and-test-a-quarkus-client-on-red-hat-codeready-containers-with-red-hat-data-grid-8-0)**
* **[Five layers of security for Red Hat Data Grid on OpenShift](https://developers.redhat.com/blog/2019/03/25/five-layers-of-security-for-red-hat-data-grid-on-openshift)**
