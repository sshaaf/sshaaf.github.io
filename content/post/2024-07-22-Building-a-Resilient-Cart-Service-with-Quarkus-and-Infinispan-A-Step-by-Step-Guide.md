---
title: "Building a Resilient Cart Service with Quarkus and Infinispan Cache: A Step-by-Step Guide"
date: 2024-07-22
image: "/images/2024/07/22/vaporware-old-school-pentium.jpeg"
tags: ["java", "cache", "infinispan", "high-availability"]
categories: ["Java"]
---

The article is a comprehensive guide on creating, deploying, and managing the [coolstore](https://github.com/sshaaf/coolstore-quarkus) cart service using Quarkus and [Infinispan](https://infinispan.org/). The guide details building the cart-service with [Quarkus](https://quarkus.io/), packaging it, and deploying it to [OpenShift](https://www.redhat.com/en/technologies/cloud-computing/openshift). 
It covers single-site deployment with Infinispan cache configuration and extends to cross-site clustering for data replication and fault tolerance across multiple data centers. 
The article also addresses schema management and implementing fault tolerance with [Smallrye Fault Tolerance](https://smallrye.io/docs/smallrye-fault-tolerance/6.2.0/index.html) for fallback mechanisms acorss multiple site deployments.
 

# What is Infinispan
> Infinispan is an open-source in-memory database that can hold nearly any type of data, from plain-text to structured objects. Retrieve your data with lightning-fast speeds with Infinispan's powerful full-text and vector search capabilities. Guarantee reliability and integrity by distributing your data across elastically scalable Infinispan clusters that offer high availability, fault tolerance, and the ability to replicate between multiple geographic sites. Connect to Infinispan using either a native, high-performance protocol or a Redis or Memcached client of your choice. 


Infinispan is a great tool for setting up distributed caching, using Quarkus we can enhance that experience. This article is a thorough walkthrough for developing a cart service using Quarkus and Infinispan. If you are a developer looking to quickly create a Kubernetes friendly multicore caching system that spans across clusters and sites, read on.. 
The article is a long overdue follow up from a talk demo I did for the Devnation Day ([playlist](https://www.youtube.com/watch?v=6-bcVni0ej8&list=PLf3vm0UK6HKpNrHaILLCMitayjfnCAy41)).
{{< youtube KT5yWwGEaDk >}}

# Cart service
Cart is a simple service that at this point creates a cart and saves either 0 or more products in the cart. 

```json
{"cartItemTotal":0.0,"cartItemPromoSavings":0.0,"shippingTotal":0.0,"shippingPromoSavings":0.0,"cartTotal":0.0,"cartId":"1fa842e1-077a-4c09-85c5-a12288c2be7e","cartItemList":[]}
```
A simple `GET` call like this `http://localhost:8084/api/cart/v2/1fa842e1-077a-4c09-85c5-a12288c2be7e` 
Where the `CartID` is inserted will create and initialize a new cart. 
The [coolstore-fe](https://github.com/sshaaf/coolstore-quarkus/blob/main/coolstore-fe/src/app/services/local.service.ts) uses the [uuidv4](https://www.npmjs.com/package//uuid) to generate uuid per browser instance.
Everytime a new coolstore-fe instance is created, it will generate a uuid and make a call to the cart-service to initialize the cart with 0 items.

## Class Diagram
![Class Diagram](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/sshaaf/coolstore-quarkus/main/docs/cart/images/cart.plantuml)

The architecture and relationships of the classes within the shopping cart service as follows:

1. **Cart**:
   - Attributes: `cartId`, `cartItemList`, `cartItemPromoSavings`, `cartItemTotal`, `shippingTotal`, `shippingPromoSavings`, `cartTotal`.
   - Contains multiple `CartItem` objects.

2. **CartItem**:
   - Attributes: `price`, `quantity`, `promoSavings`, `product`.
   - Associated with a `Product`.

3. **CartService**:
   - Interface implemented by `CartServiceImpl`.
   - Methods: `getShoppingCart`, `priceShoppingCart`.

4. **CartServiceImpl**:
   - Implements `CartService`.
   - Interacts with `ShippingService`, `PromotionService`, and a `RemoteCache` of `Cart` objects.
   - Handles business logic for cart operations.

5. **CartResourceV1** and **CartResourceV2**:
   - REST API endpoints for cart service.
   - Dependency on `CartService`.

6. **Product**:
   - Attributes: `itemId`, `name`, `desc`, `price`.

7. **Promotion**:
   - Attributes: `itemId`, `percentOff`.

8. **Order**:
   - Attributes: billing details, includes a `CreditCard`.

The `CartServiceImpl` manages interactions between cart items, promotions, and shipping calculations.


## Deploying on a single site
The following instructions assume that the infinispan operator is pre-installed.
Incase you want to use the cart only on one instance. To use the cache only on site nyc without backup
Create the following CR in the namepsace

```yaml
apiVersion: infinispan.org/v1
kind: Infinispan 
metadata:
  name: nyc 
  namespace: nyc
spec:
  replicas: 2
  expose:
    type: Route
```
Create a cache in the DG/Infinispan server
![Create Cache](/images/2024/07/22/nyc-local.png)

Press `Next` and load the following configuration for the cache.

```json
{
    "distributed-cache": {
        "mode": "SYNC",
        "owners": 2,
        "statistics": true,
        "encoding": {
            "media-type": "application/x-protostream"
        },
        "locking": {
            "isolation": "REPEATABLE_READ"
        }
    }
}
```
The [application.properties](src/main/resources/application.properties) defines the following attributes to connect to a DG/Infinispan cluster

```properties
%prod.quarkus.infinispan-client.hosts=nyc.nyc.svc.cluster.local:11222
%prod.quarkus.infinispan-client.use-auth=true
%prod.quarkus.infinispan-client.username=developer
%prod.quarkus.infinispan-client.password=XXXXXX
%prod.quarkus.infinispan-client.trust-store=/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt
%prod.quarkus.infinispan-client.trust-store-type=pem
```

Ensure you have the correct host and password configured in the cart-service. the [section](#Commands) also describes how to get those details. 
Once set you can now deploy an instance of your cart-service into OpenShift by issuing the following Command

```bash
mvn clean compile package -Dquarkus.kubernetes.deploy=true
```

Once deployed call the cart-service via curl as follows.
```bash
curl -X GET http://CART-SERIVCE-ROUTE/api/cart/v2/1fa842e1-077a-4c09-85c5-a12288c2be77
{"cartItemTotal":0.0,"cartItemPromoSavings":0.0,"shippingTotal":0.0,"shippingPromoSavings":0.0,"cartTotal":0.0,"cartId":"1fa842e1-077a-4c09-85c5-a12288c2be77","cartItemList":[]}
```

## Infinispan Cross-site cluster deployment
Cross-site clustering in Infinispan is a feature that enables data replication and synchronization across multiple geographically distributed clusters or data centers.
The primary goal of cross-site clustering is to ensure data availability and fault tolerance in the event of failures or disasters affecting a single cluster or data center. By replicating data across multiple sites, Infinispan provides redundancy and enables high availability of data even when one or more sites become unavailable.
Here's a high-level overview of how cross-site clustering works in Infinispan:

- Data Centers and Clusters: Infinispan allows you to set up multiple data centers, each consisting of one or more clusters. A cluster represents a group of nodes (servers) that work together to store and process data.
- Site and Backup Site: In cross-site clustering, each data center is typically associated with a site, and within each site, there can be one or more clusters. Additionally, one of the sites is designated as the backup site.
- Data Replication: Infinispan replicates data across clusters within the same site and also across clusters in different sites. This replication is typically asynchronous, meaning that updates made at one site are eventually propagated to other sites.
- Replication Modes: Infinispan supports different replication modes for cross-site clustering, including synchronous and asynchronous modes. In synchronous mode, updates are replicated immediately to other sites before confirming the success of the operation. In asynchronous mode, updates are sent to other sites in the background without waiting for confirmation.
- Consistency Models: Infinispan also provides various consistency models to control the level of data consistency across sites. For example, strong consistency ensures that updates are seen in the same order at all sites, while eventual consistency allows for some level of inconsistency for improved performance.
- Failure Detection and Recovery: Infinispan monitors the health and availability of nodes, clusters, and sites. If a site or cluster becomes unavailable, Infinispan automatically redirects read and write operations to the backup site or other available clusters to ensure data access and continued operations.

By leveraging cross-site clustering in Infinispan, one can achieve improved data availability, disaster recovery, and fault tolerance. It allows them to distribute their data across multiple locations, ensuring that even if one site or cluster goes down, the data remains accessible and consistent from other sites.

This section is a guide to deploying the Cart in a cross site cluster.
- NYC
- LON


### Deploying the CRs
Infinispan Operator in one data center can discover a Infinispan cluster that another Infinispan Operator manages in another data center. This discovery allows Infinispan to automatically form cross-site views and create global clusters.

The following illustration provides an example in which Infinispan Operator manages a Infinispan cluster at a data center in New York City, NYC. At another data center in London, LON, a Infinispan Operator also manages a Infinispan cluster.

![Cross site Topology](/images/2024/07/22/cross-site-topology.png)

Infinispan Operator uses the Kubernetes API to establish a secure connection between the OpenShift Container Platform clusters in NYC and LON. Infinispan Operator then creates a cross-site replication service so that Infinispan clusters can back up data across locations.

Each Infinispan cluster has one site master node that coordinates all backup requests. Infinispan Operator identifies the site master node so that all traffic through the cross-site replication service goes to the site master.


Assuming the Infinispan or Infinispan operator is already installed on the cluster or in both the namespaces. Run the following CRs


- Namespace: nyc

```yaml

apiVersion: infinispan.org/v1
kind: Infinispan
metadata:
  name: nyc
spec:
  replicas: 2
  expose:
    type: Route
  logging:
    categories:
      org.jgroups.protocols.TCP: error
      org.jgroups.protocols.relay.RELAY2: error
  service:
    container:
      storage: 1Gi
    sites:
      local:
        expose:
          type: ClusterIP
        name: NYC
      locations:
        - clusterName: lon
          name: LON
          namespace: lon
          secretName: lon-token
          url: 'infinispan+xsite://lon-site.user1-cache2.svc:7900'
    type: DataGrid
```



- Namespace: lon

```yaml

apiVersion: infinispan.org/v1
kind: Infinispan
metadata:
  name: lon
spec:
  replicas: 2
  expose:
    type: Route
  logging:
    categories:
      org.jgroups.protocols.TCP: error
      org.jgroups.protocols.relay.RELAY2: error
  service:
    container:
      storage: 1Gi
    sites:
      local:
        expose:
          type: ClusterIP
        name: LON
      locations:
        - clusterName: nyc
          name: NYC
          namespace: nyc
          secretName: lon-token
          url: 'infinispan+xsite://nyc-site.nyc.svc:7900'
    type: DataGrid
``` 

To create a cache that will span across NYC and LON. 

Create the following cache in NYC cluster by logging into the DG/Infinispan console.
For details on your deployed cluster [section](#Commands)


![Create Cache](../docs/cart/images/nyc-local.png)

Press `Next` and load the following configuration for the cache.


```json
{
  "carts": {
    "replicated-cache": {
      "mode": "SYNC",
      "remote-timeout": "17500",
      "statistics": true,
      "backups": {
        "LON": {
          "backup": {
            "strategy": "ASYNC",
            "take-offline": {
              "min-wait": "120000"
            }
          }
        }
      },
      "encoding": {
        "media-type": "application/x-protostream"
      },
      "locking": {
        "concurrency-level": "1000",
        "acquire-timeout": "15000",
        "striping": false
      },
      "state-transfer": {
        "timeout": "60000"
      }
    }
  }
}
``` 

And the following also to be created in the similar fashion in the LON DG/Infinispan console.

```json
{
"carts": {
    "distributed-cache": {
      "mode": "SYNC",
      "backups": {
        "NYC": {
          "backup": {
            "strategy": "SYNC",
            "take-offline": {
              "min-wait": "120000"
            }
          }
        }
      },
      "encoding": {
        "media-type": "application/x-protostream"
      }
    }
}
}
``` 


When a back cluster is defined, the Quarkus app does not upload the schema into the backup site. Schemas are global and can be used by multiple caches.
However, if the schema does not exist in the backup site, the DG/Infinispan wouldn't really identify it and we wont see it. https://github.com/quarkusio/quarkus/issues/34435

Create a new Schema in the LON backup site. using the following config.
Proto schema
```protobuf

// File name: CartContextInitializer.proto
// Generated from : org.coolstore.cart.cache.CartContextInitializer

syntax = "proto2";
package coolstore;

message Product {
    optional string itemId = 1;
    optional string name = 2;
    optional string desc = 3;
    optional double price = 4 [default = 0.0];
}

message Cart {
    optional string cartId = 1;
    repeated CartItem cartItemList = 2;
    optional double cartItemTotal = 3 [default = 0.0];
    optional double shippingTotal = 4 [default = 0.0];
    optional double cartTotal = 5 [default = 0.0];
    optional double cartItemPromoSavings = 6 [default = 0.0];
    optional double shippingPromoSavings = 7 [default = 0.0];
}


message CartItem {
    optional Product product = 1;
    optional double price = 2 [default = 0.0];
    optional int32 quantity = 3 [default = 0];
    optional double promoSavings = 4 [default = 0.0];
}


message Promotion {
    optional string itemId = 1;
    optional double percentOff = 2 [default = 0.0];
}
```

Once all of the above is done; now deploy an instance of the cart-service into OpenShift by issuing the following Command

```bash
mvn clean compile package -Dquarkus.kubernetes.deploy=true
```

Once deployed call the cart-service via curl as follows.
```bash
curl -X GET http://CART-SERIVCE-ROUTE/api/cart/v2/1fa842e1-077a-4c09-85c5-a12288c2be77
{"cartItemTotal":0.0,"cartItemPromoSavings":0.0,"shippingTotal":0.0,"shippingPromoSavings":0.0,"cartTotal":0.0,"cartId":"1fa842e1-077a-4c09-85c5-a12288c2be77","cartItemList":[]}⏎
```

At this point everything that will be written to the cache in NYC will also be replicated directly to LON. 


The distributed nature of microservices presents a challenge in terms of reliable communication with external systems, 
placing greater emphasis on the resilience of applications. To facilitate the development of more resilient applications, 
Quarkus offers [Smallrye Fault tolerance](https://quarkus.io/guides/smallrye-fault-tolerance), which implements the MicroProfile Fault Tolerance specification.
In a scenario where our primary site does not respond we can use this extension to fallback to the backup site. 

In the [CartServiceImpl](src/main/java/org/coolstore/cart/service/CartServiceImpl.java)
- Inject two clients `site-nyc`, `site-lon`
- add a maybefail method that is randomly(boolean) simulating a failure by randomly throwing a RuntimeException.
- The `fallbackCache(String cartId)` needs to be added to call the code when the service fallback
- The `getShoppingCart(String cartId)` also needs to be changed to add the annotation to fallback and calling our random maybefail method.

```java

    // primary
    @Inject
    @InfinispanClientName("site-nyc")
    @Remote(CART_CACHE)
    RemoteCache<String, Cart> carts;



    @Inject
    @InfinispanClientName("site-lon")
    @Remote(CART_CACHE)
    RemoteCache<String, Cart> cartsBkp;


    private void maybeFail(String failureLogMessage) {

        if (new Random().nextBoolean()) {
            log.error(failureLogMessage);
            throw new RuntimeException("Resource failure.");
        }
    }



    public Cart fallbackCache(String cartId) {

        log.info("Falling back to the backup cache...");
        // safe bet, return something that everybody likes

        if (!cartsBkp.containsKey(cartId)) {
            Cart cart = new Cart(cartId);
            cartsBkp.put(cartId, cart);
            return cart;
        }

        Cart cart = cartsBkp.get(cartId);
        priceShoppingCart(cart);
        cartsBkp.put(cartId, cart);
        return cart;
    }


    @Override
    @Fallback(fallbackMethod = "fallbackCache")
    public Cart getShoppingCart(String cartId) {
        maybeFail("trying to failover.....");
        if (!carts.containsKey(cartId)) {
            Cart cart = new Cart(cartId);
            carts.put(cartId, cart);
            return cart;
        }

        Cart cart = carts.get(cartId);
        priceShoppingCart(cart);
        carts.put(cartId, cart);
        return cart;
    }
```

Perfect now that the service is ready to fallback between NYC and LON. It also needs to be deployed.
The [application.properties](src/main/resources/application.properties) defines the following attributes to connect to a DG/Infinispan cluster

```properties
%prod.quarkus.infinispan-client.site-nyc.hosts=nyc.nyc.svc.cluster.local:11222
%prod.quarkus.infinispan-client.site-nyc.username=developer
%prod.quarkus.infinispan-client.site-nyc.password=XXXXXXXXXX
%prod.quarkus.infinispan-client.site-nyc.trust-store=/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt
%prod.quarkus.infinispan-client.site-nyc.trust-store-type=pem

%prod.quarkus.infinispan-client.site-lon.hosts=lon.lon.svc.cluster.local:11222
%prod.quarkus.infinispan-client.site-lon.username=developer
%prod.quarkus.infinispan-client.site-lon.password=XXXXXXXXXX
%prod.quarkus.infinispan-client.site-lon.trust-store=/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt
%prod.quarkus.infinispan-client.site-lon.trust-store-type=pem

```

Once all of the above is done; now deploy an instance of the cart-service into OpenShift by issuing the following Command

```bash
mvn clean compile package -Dquarkus.kubernetes.deploy=true
```

Once deployed call the cart-service via curl as follows.
```bash
curl -X GET http://CART-SERIVCE-ROUTE/api/cart/v2/1fa842e1-077a-4c09-85c5-a12288c2be77
{"cartItemTotal":0.0,"cartItemPromoSavings":0.0,"shippingTotal":0.0,"shippingPromoSavings":0.0,"cartTotal":0.0,"cartId":"1fa842e1-077a-4c09-85c5-a12288c2be77","cartItemList":[]}⏎
```

Hit the curl command multiple times. and check the logs on cart-service. the `maybefail` method logs the fallback in action.


### Commands
Run the following command to get the status of the cluster
```bash
$ kubectl get infinispan -o yaml
```

The response indicates that datagrid nodes have received clustered views, as in the following example:
```bash
conditions:
    - message: 'View: nyc-0-25302,nyc-1-19194'
      status: "True"
      type: WellFormed
```

You can also wait for the condition check:

```bash
$ kubectl wait --for condition=wellFormed --timeout=240s infinispan/nyc
```

Let’s retrieve cluster view from logs as follows:
```bash
kubectl logs nyc-0 | grep ISPN000094
10:37:12,856 INFO  (main) [org.infinispan.CLUSTER] ISPN000094: Received new cluster view for channel nyc: [nyc-1-19194|5] (2) [nyc-1-19194, nyc-0-25302]
```

To get the route and access the DG console:
```bash
$ oc get routes
nyc-external        nyc-external-nyc.xxxxxxx.com               nyc                 11222      passthrough   None
```

To get the secret
```bash
$ kubectl get secret nyc-generated-secret -o jsonpath="{.data.identities\.yaml}" | base64 --decode
credentials:
- username: developer
  password: ....
  roles:
  - admin
```

And that's all folks! 