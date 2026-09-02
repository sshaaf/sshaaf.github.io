---
title:       "Decomposing a Monolith into Microservices with Call Graph Analysis"
subtitle:    "Finding service boundaries with community detection and blast radius"
description: "A concrete decomposition of a Java EE monolith into microservices using rgctl's community detection, blast radius analysis, and CPG field mutation tracking to identify natural service boundaries and quantify coupling at each cut."
date:        2026-09-01
image:       "/images/2026/09/decomposing-a-monolith-into-microservices-with-call-graph-analysis-1.jpg"
tags:        ["rust", "java", "microservices", "rgctl", "call-graph", "architecture"]
categories:  ["Java", "Rust"]
layout: post
type: post
devto: true
---

# Decomposing a Monolith into Microservices with Call Graph Analysis

Splitting a monolith into microservices is a problem of finding boundaries. The
wrong boundaries produce distributed monoliths -- microservices that cannot be
deployed independently because they call each other synchronously for every
operation. The right boundaries follow natural seams in the code: clusters of
functions that are tightly coupled internally but loosely connected to the rest
of the system. This post picks up the CoolStore monolith from
[migrating it to Quarkus with rgctl](https://shaaf.dev/post/migrating-coolstore-monolith-to-quarkus-with-rgctl/)
and applies the same graph analysis to the next question: where to cut it into
services.

This post walks through a concrete decomposition of a Java EE monolith using
static call-graph analysis. I use [rgctl](https://github.com/sshaaf/rgctl)
to build the function-level call graph, detect community structure, measure
coupling with blast radius, and identify the cuts that produce viable
microservice boundaries. The goal is not to argue that you should decompose
every monolith -- it is to show how graph analysis replaces intuition with
structural evidence when you decide to.

> before we move forward, yes you can use the same functionality in tandem with an code agent as well. This is possible by using the skill provided by rgctl. The following [guide explains how the skill works](https://shaaf.dev/rgctl/docs/guides/agent-skill/) and how to install it.


## The Monolith

The CoolStore is a Java EE 7 e-commerce application originally deployed on
WebLogic. It has 25 classes across 5 packages:

![CoolStore monolith package layout](/images/2026/09/coolstore-monolith-packages.svg)

The application handles four distinct business operations:

1. **Catalog browsing** -- list products, look up inventory
2. **Shopping cart** -- add/remove items, price calculation, shipping, promotions
3. **Order processing** -- checkout publishes to JMS, MDBs persist the order
4. **Inventory management** -- deduct stock on order, low-stock alerts

In the monolith, these operations share a single database, a single JMS topic,
and freely inject each other's EJBs. The question is: which of these can become
independent services, and where are the coupling points that make that hard?

## Step 1: Build the Call Graph

All commands below assume the rgctl repository root, with the CoolStore example
at `example/coolstore-weblogic`.

```bash
$ rgctl -r example/coolstore-weblogic discover . \
    --with-cfg \
    --with-harmonic \
    --with-security \
    --export-migration-hints
```

```
[>] rgctl discover
[!] Deep analysis enabled (--with-cfg / --with-taint).
[✓] Loaded 1227 files from snapshot -> 17417 nodes, 52920 edges
[✓] Analyzed 7526 functions (avg complexity: 1.0)
[✓] Detected 13565 communities (modularity: 0.29)
[!] Found 186 circular dependencies

✓ Security analysis:
  Potential secrets found: 5

✓ Control flow analysis:
  Field writes indexed: 3299
  CFG/PDG/Dominance: 6585 functions analyzed
  Skipped: 941 functions (unsupported language or parse error)

[✓] rgctl discover finished in 16.4s
```

186 circular dependencies. In a monolith, this is typical -- EJBs inject each
other, services call back into the REST layer, model objects are passed across
every boundary. But for microservice decomposition, every circular dependency
is a potential distributed coupling problem. I need to find which cycles can
be broken and which are load-bearing.

## Step 2: Detect Community Structure

rgctl uses label-propagation community detection on the call graph. This
algorithm finds clusters of functions that call each other densely but have
sparse connections to the outside. These clusters are candidates for
microservice boundaries.

```bash
$ rgctl -r example/coolstore-weblogic -f json gql --macro-name all_communities unused
```

Filtering to communities with 2+ members that contain Java application code
(community IDs are assigned at `discover` time; labels are the stable handle
when comparing runs on the same snapshot):

| Community | Members | Label | Dominant Classes |
|-----------|---------|-------|------------------|
| 8064 | 30 | `coolstore.model::`<br>`APPLICATION_JSON` | CartEndpoint, ShoppingCartService, ShoppingCart, ShippingService, PromoService |
| 4266 | 30 | `coolstore.model::`<br>`getCartItemTotal` | ShoppingCartService, ShippingService, PromoService, Transformers |
| 11973 | 18 | `coolstore.model::`<br>`getProductByItemId` | ProductEndpoint, ProductService, Transformers, Product, CatalogItemEntity |
| 11250 | 7 | `coolstore.service::`<br>`CatalogItemEntity` | CatalogService, InventoryEntity |
| 4058 | 4 | `coolstore.service::`<br>`getPercentOff` | PromoService, Promotion |
| 14643 | 5 | `coolstore.rest::Order` | OrderEndpoint, OrderService |

Let's look at what the community detection is telling me by examining the
members of each cluster.

### Community 8064 (30 members): Cart Operations

```bash
$ rgctl -r example/coolstore-weblogic -f json gql \
    "MATCH (f:Function) WHERE f.community_id = '8064' RETURN f LIMIT 50"
```

```
CartEndpoint.add             CartEndpoint.delete
CartEndpoint.set             CartEndpoint.dedupeCartItems
CartEndpoint.getCart         CartEndpoint.checkout
ShoppingCartService.getShoppingCart   ShoppingCartService.getProduct
ShoppingCart.addShoppingCartItem      ShoppingCart.removeShoppingCartItem
ShoppingCart.getShoppingCartItemList  ShoppingCart.setShoppingCartItemList
ShoppingCartItem.setQuantity         ShoppingCartItem.setPrice
ShoppingCartItem.setProduct          ShoppingCartItem.getQuantity
ShoppingCartItem.toOrderItem         Product.getPrice
```

This is the cart CRUD cluster -- adding, removing, and listing items. The
algorithm grouped the REST endpoint, the service, and the relevant model
methods into one community because they form a tight call cycle.

### Pricing and Shipping (community 4266)

```
ShoppingCartService.priceShoppingCart   ShoppingCartService.initShoppingCartForPricing
ShoppingCartService.lookupShippingServiceRemote
ShippingService.calculateShipping      ShippingService.calculateShippingInsurance
ShippingService.getPercentOfTotal
PromoService.applyShippingPromotions
ShoppingCart.getCartItemTotal          ShoppingCart.setCartItemTotal
ShoppingCart.setShippingTotal          ShoppingCart.getShippingTotal
ShoppingCart.setCartTotal              ShoppingCart.setCartItemPromoSavings
ShoppingCartItem.getPromoSavings
ShoppingCart.setShippingPromoSavings
```

This is the pricing engine -- computing totals, shipping costs, and
applying shipping promotions. It pulls in `ShippingService` and
`PromoService.applyShippingPromotions` because `priceShoppingCart` calls both
directly.

### Cart Serialization and Item Promotions

```
ShoppingCartOrderProcessor.process
Transformers.shoppingCartToJson        Transformers.$lambda$0
Transformers.$lambda$1
PromoService.applyCartItemPromotions   PromoService.getPromotions
Promotion.getPercentOff                Promotion.getItemId
ShoppingCartItem.setPromoSavings
ShoppingCart.getCartItemPromoSavings    ShoppingCart.getCartTotal
ShoppingCart.getShippingPromoSavings
```

This cluster links cart serialization (for JMS publishing) with item-level
promotions. The connection is through `ShoppingCartOrderProcessor.process`,
which serializes the cart, and `PromoService.applyCartItemPromotions`, which
reads and writes cart item prices.

### Order Fulfillment and Inventory (community 11250 + order MDB cluster)

```
OrderServiceMDB.onMessage             OrderServiceMDB.$lambda$0
InventoryNotificationMDB.onMessage    InventoryNotificationMDB.$lambda$0
OrderService.save
CatalogService.getCatalogItemById     CatalogService.updateInventoryItems
CatalogItemEntity.getInventory
InventoryEntity.getQuantity           InventoryEntity.setQuantity
Order.getItemList                     OrderItem.getProductId
```

This is the order fulfillment pipeline -- the two MDBs that listen on the JMS
topic, persist the order, and update inventory. `CatalogService` appears here
because both MDBs use it: `OrderServiceMDB` calls `updateInventoryItems` and
`InventoryNotificationMDB` calls `getCatalogItemById` to check stock levels.

### Product Catalog (community 11973)

```
ProductEndpoint.listAll               ProductEndpoint.getProduct
ProductService.getProducts            ProductService.getProductByItemId
ProductService.$lambda$0
CatalogService.getCatalogItems
Transformers.toProduct
Product.setItemId  Product.setPrice  Product.setLocation
Product.setQuantity  Product.setLink  Product.setDesc  Product.setName
```

Product listing and lookup. `CatalogService.getCatalogItems` provides the JPA
query, `Transformers.toProduct` maps entities to DTOs, and `ProductEndpoint`
exposes the REST API.

### Order Queries (community 14643)

```
OrderEndpoint.listAll      OrderEndpoint.getOrder
OrderService.getOrders     OrderService.getOrderById
```

Simple read path for orders. Just an endpoint and a service with JPA queries.

## Step 3: Map the Proposed Microservice Boundaries

The communities suggest four natural services, but with complications. Let me
map them out and then use blast radius to quantify the coupling at each boundary.

### Proposed services

Based on the community structure:

![Proposed microservice boundaries from community detection](/images/2026/09/coolstore-proposed-services.svg)

The communities group naturally into three services. But look at the problems:

1. **`CatalogService` appears in two communities** -- it is called by the
   product listing path (community 11973) and by the order fulfillment path
   (community 11250 -- MDBs call `CatalogService` for inventory operations).

2. **`Transformers` is split across three services** -- `toProduct` belongs
   with catalog, `shoppingCartToJson` with cart, `jsonToOrder` with orders.

3. **`PromoService` spans two communities** -- `applyCartItemPromotions`
   is in community 4058 (item promotions) and `applyShippingPromotions` is
   in community 4266 (pricing and shipping).

4. **`ShoppingCartService.getProduct`** calls `ProductService.getProductByItemId`
   -- a synchronous cross-service call.

These are not trivial issues. They are the structural coupling that makes
monolith decomposition hard. Let's use blast radius to quantify them.

## Step 4: Quantify Coupling with Blast Radius

Blast radius tells you: if I change this function, how many upstream callers
break? For microservice decomposition, I care specifically about functions that
are called across the proposed service boundaries -- these become the API
contracts between services.

### Cross-boundary calls

Query the call graph for edges between Java classes:

```bash
$ rgctl -r example/coolstore-weblogic -f json gql \
    "MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a,b LIMIT 5000"
```

Filtering to cross-class calls between Java files, the significant
inter-service edges are:

| Source (proposed service) | Target (proposed service) | Call |
|---------------------------|---------------------------|------|
| Cart | Catalog | `ShoppingCartService.getProduct`<br>→ `ProductService.getProductByItemId` |
| Cart | Catalog | `ShoppingCartOrderProcessor.process`<br>→ `Transformers.shoppingCartToJson` (shared) |
| Order | Catalog | `OrderServiceMDB.onMessage`<br>→ `CatalogService.updateInventoryItems` |
| Order | Catalog | `InventoryNotificationMDB.onMessage`<br>→ `CatalogService.getCatalogItemById` |
| Order | Cart | `Transformers.jsonToOrder` (shared code, both need it) |

### Blast radius at the boundaries

Now let's check the impact of the key boundary functions:

```bash
$ rgctl -r example/coolstore-weblogic -f json blast-radius getShoppingCart
$ rgctl -r example/coolstore-weblogic -f json blast-radius priceShoppingCart
$ rgctl -r example/coolstore-weblogic -f json blast-radius getCatalogItems
$ rgctl -r example/coolstore-weblogic -f json blast-radius getProducts
$ rgctl -r example/coolstore-weblogic -f json blast-radius toProduct
$ rgctl -r example/coolstore-weblogic -f json blast-radius save --class OrderService
$ rgctl -r example/coolstore-weblogic -f json blast-radius onMessage --class OrderServiceMDB
$ rgctl -r example/coolstore-weblogic -f json blast-radius calculateShipping --file ShippingService.java
```

| Function | Score | Direct Callers | Impact Zone | Proposed Service |
|----------|-------|----------------|-------------|------------------|
| `ShoppingCartService::`<br>`getShoppingCart` | 40.5 | 6 | 10 | Cart |
| `ShoppingCartService::`<br>`priceShoppingCart` | 40.4 | 5 | 7 | Cart |
| `ProductService::`<br>`getProducts` | 40.1 | 2 | 2 | Catalog |
| `Transformers::`<br>`toProduct` | 40.7 | 2 | 14 | Catalog |
| `Transformers::`<br>`jsonToOrder` | 40.1 | 2 | 2 | Order |
| `Transformers::`<br>`shoppingCartToJson` | 25.2 | 1 | 4 | Cart |
| `PromoService::`<br>`applyCartItemPromotions` | 25.4 | 1 | 8 | Cart |
| `CatalogService::`<br>`getCatalogItems` | 25.1 | 1 | 3 | Catalog |
| `CatalogService::`<br>`updateInventoryItems` | 25.1 | 1 | 1 | Catalog |
| `OrderService::save` | 25.1 | 1 | 1 | Order |
| `OrderServiceMDB::`<br>`onMessage` | 0.0 | 0 | 0 | Order |
| `ShippingService::`<br>`calculateShipping` | 0.0 | 0 | 0 | Cart |

`Transformers::toProduct` has the highest blast radius at 40.7 with 14 nodes in
the impact zone. This is a utility function that maps JPA entities to DTOs. It
is called by both `ProductService.getProducts` (catalog browsing) and
`ProductService.getProductByItemId` (called from the cart service). If you
change this function, 14 upstream functions are affected -- across two proposed
service boundaries.

### What the ShoppingCart mutations tell me

I can also use CPG field mutation analysis to understand the data coupling:

```bash
$ rgctl -r example/coolstore-weblogic -f json cpg mutations --type ShoppingCart --exclude-ctors
```

```json
{
  "mutations": [
    {"function": "setShoppingCartItemList", "member": "shoppingCartItemList", "kind": "ThisField"},
    {"function": "setCartItemTotal",        "member": "cartItemTotal",        "kind": "ThisField"},
    {"function": "setShippingTotal",        "member": "shippingTotal",        "kind": "ThisField"},
    {"function": "setCartTotal",            "member": "cartTotal",            "kind": "ThisField"},
    {"function": "setCartItemPromoSavings",  "member": "cartItemPromoSavings",  "kind": "ThisField"},
    {"function": "setShippingPromoSavings",  "member": "shippingPromoSavings",  "kind": "ThisField"}
  ]
}
```

Six fields are mutated on `ShoppingCart` by functions spread across community
8064 (cart CRUD) and community 4266 (pricing and shipping) and community 4058 (item promotions). The cart object
is a shared mutable structure that both `ShoppingCartService`, `PromoService`,
and `ShippingService` write to. In a monolith, this works because they all
operate on the same in-memory object. In microservices, you need to decide who
owns this state.

## Step 5: Make the Cuts

With the structural data in hand, here are the decomposition decisions and the
reasoning behind each.

### Service 1: Catalog Service

**Scope**: Product listing, inventory queries, entity-to-DTO mapping.

**Classes**:
- `ProductEndpoint` (REST API)
- `ProductService` (business logic)
- `CatalogService` (JPA queries) -- but only the read path:
  `getCatalogItems`, `getCatalogItemById`
- `CatalogItemEntity`, `InventoryEntity` (JPA entities)
- `Product` (DTO)
- `Transformers.toProduct` (mapping logic -- inlined into this service)

**Why these boundaries work**: Communities 11973 and 11250 form a clean cluster
with only one outbound dependency: `ProductService` is called by
`ShoppingCartService.getProduct` in the cart service.

**API contract**: Expose a REST endpoint that the cart service calls instead of
injecting `ProductService` directly:

```java
// Catalog Service: src/main/java/com/redhat/coolstore/catalog/ProductResource.java
@Path("/api/products")
@ApplicationScoped
public class ProductResource {

    @Inject
    ProductService productService;

    @GET
    @Produces(MediaType.APPLICATION_JSON)
    public List<Product> listAll() {
        return productService.getProducts();
    }

    @GET
    @Path("/{itemId}")
    @Produces(MediaType.APPLICATION_JSON)
    public Product getByItemId(@PathParam("itemId") String itemId) {
        return productService.getProductByItemId(itemId);
    }
}
```

**Blast radius validation**: `getCatalogItems` has a score of 25.1 with only 1
direct caller (`ProductService.getProducts`). This call stays within the
service. The cross-service call from `ShoppingCartService.getProduct` ->
`ProductService.getProductByItemId` becomes a REST client call, which is a clean
boundary.

### Service 2: Cart Service

**Scope**: Shopping cart lifecycle, pricing, shipping, promotions, checkout
trigger.

**Classes**:
- `CartEndpoint` (REST API)
- `ShoppingCartService` (cart operations + pricing)
- `ShippingService` (shipping cost calculation)
- `PromoService` (promotion rules)
- `ShoppingCartOrderProcessor` (publishes checkout event)
- `ShoppingCart`, `ShoppingCartItem`, `Promotion` (model objects)

**Why these boundaries work**: Communities 8064 and 4266 (plus community 4058 for item
promotions) forms the cart operations cluster. Despite label-propagation
sometimes splitting cart, pricing, and promotions into adjacent communities,
they share a tight internal coupling: `priceShoppingCart` calls both
`ShippingService` and `PromoService`, and `checkOutShoppingCart` calls
`ShoppingCartOrderProcessor`. These are all synchronous, performance-sensitive
calls that belong together.

**The CatalogService coupling**: `ShoppingCartService.getProduct` calls
`ProductService.getProductByItemId`, which calls
`CatalogService.getCatalogItemById`. This is the only synchronous cross-service
dependency from cart to catalog. Replace the EJB injection with a REST client:

```java
// Cart Service: replaces the direct ProductService injection
@ApplicationScoped
public class CatalogClient {

    @Inject
    @RestClient
    CatalogApi catalogApi;

    public Product getProduct(String itemId) {
        return catalogApi.getByItemId(itemId);
    }
}

@RegisterRestClient(configKey = "catalog-api")
@Path("/api/products")
public interface CatalogApi {

    @GET
    @Path("/{itemId}")
    Product getByItemId(@PathParam("itemId") String itemId);
}
```

```properties
# application.properties
quarkus.rest-client.catalog-api.url=http://catalog-service:8080
```

**Checkout becomes an event**: `ShoppingCartOrderProcessor.process` currently
publishes to a JMS topic. In the microservices version, this becomes a message
to a shared broker (Kafka or AMQP). The cart service is the producer; the order
service is the consumer. This is already an asynchronous boundary in the
monolith -- JMS was doing the right thing.

```java
// Cart Service: checkout event publisher
@ApplicationScoped
public class ShoppingCartOrderProcessor {

    @Inject
    @Channel("orders-out")
    Emitter<String> ordersEmitter;

    public void process(ShoppingCart cart) {
        ordersEmitter.send(Transformers.shoppingCartToJson(cart));
    }
}
```

**Blast radius validation**: `getShoppingCart` has a score of 40.5, but all 6
direct callers are within the cart service (`CartEndpoint.add`, `.delete`,
`.set`, `.getCart`, `.dedupeCartItems`, and `ShoppingCartService.checkOutShoppingCart`).
The blast radius stays internal. The only outbound edge is the checkout event,
which is asynchronous.

### Service 3: Order Service

**Scope**: Order persistence, order queries, inventory deduction, low-stock
alerts.

**Classes**:
- `OrderEndpoint` (REST API for order queries)
- `OrderService` (JPA persistence for orders)
- `OrderServiceMDB` -> becomes `OrderEventConsumer` (consumes checkout events)
- `InventoryNotificationMDB` -> becomes `InventoryAlertConsumer`
- `Order`, `OrderItem` (JPA entities)

**Why these boundaries work**: The order MDB cluster and communities 11250 and 14643 form the
order processing cluster. The MDBs have blast radius 0.0 -- they are pure
consumers with no upstream callers. This makes them ideal microservice entry
points: they receive events and operate independently.

**The CatalogService coupling problem**: This is the hardest cut.
`OrderServiceMDB.onMessage` calls `CatalogService.updateInventoryItems`, and
`InventoryNotificationMDB.onMessage` calls `CatalogService.getCatalogItemById`.
Both need access to inventory data that lives in the catalog service's
database.

There are two options:

**Option A: REST call to catalog service** (simple, synchronous)

```java
@ApplicationScoped
public class OrderEventConsumer {

    @Inject
    OrderService orderService;

    @Inject
    @RestClient
    CatalogApi catalogApi;

    @Incoming("orders-in")
    public void onMessage(String orderStr) {
        Order order = Transformers.jsonToOrder(orderStr);
        orderService.save(order);
        order.getItemList().forEach(item ->
            catalogApi.updateInventory(item.getProductId(), item.getQuantity())
        );
    }
}
```

**Option B: Publish inventory events** (asynchronous, better decoupling)

```java
@ApplicationScoped
public class OrderEventConsumer {

    @Inject
    OrderService orderService;

    @Inject
    @Channel("inventory-updates")
    Emitter<String> inventoryEmitter;

    @Incoming("orders-in")
    public void onMessage(String orderStr) {
        Order order = Transformers.jsonToOrder(orderStr);
        orderService.save(order);
        // Emit inventory deduction events instead of direct call
        order.getItemList().forEach(item ->
            inventoryEmitter.send(Json.createObjectBuilder()
                .add("productId", item.getProductId())
                .add("quantity", item.getQuantity())
                .build().toString())
        );
    }
}
```

With Option B, the catalog service would consume `inventory-updates` and handle
deductions internally. This eliminates the synchronous dependency entirely.

Blast radius confirms this is safe: `OrderServiceMDB::onMessage` and
`InventoryNotificationMDB::onMessage` both have scores of 0.0. Changing their
implementation (from JMS to Reactive Messaging, from direct call to event) has
zero impact on upstream callers.

### The Shared Code Problem: Transformers

`Transformers` is the class that appears in all three services. It has three
static methods:

| Method | Blast Radius | Used By |
|--------|-------------|---------|
| `toProduct` | 40.7 | Catalog (entity-to-DTO mapping) |
| `shoppingCartToJson` | 25.2 | Cart (checkout serialization) |
| `jsonToOrder` | 40.1 | Order (event deserialization) |

These are pure functions with no state and no injected dependencies. The correct
decomposition is to split them:

- **`toProduct`** moves into the catalog service. It depends on
  `CatalogItemEntity` and `Product`, both of which are catalog-owned models.
- **`shoppingCartToJson`** moves into the cart service. It depends on
  `ShoppingCart` and `ShoppingCartItem`.
- **`jsonToOrder`** moves into the order service. It depends on `Order` and
  `OrderItem`.

Each method only references model classes owned by its target service. The blast
radius scores confirm this is the right split: each method's callers are entirely
within its target service.

### The Shared Model Problem

In the monolith, `ShoppingCart`, `Order`, `Product`, and their related classes
are all in one `model` package. In the decomposed version, each service owns its
domain model:

| Service | Owned Models |
|---------|-------------|
| Catalog | `CatalogItemEntity`, `InventoryEntity`, `Product` |
| Cart | `ShoppingCart`, `ShoppingCartItem`, `Promotion` |
| Order | `Order`, `OrderItem` |

The boundary is clean except for one thing: `Product` is used by both the
catalog service (as a DTO returned by the API) and the cart service (as the
product embedded in a `ShoppingCartItem`). The solution is standard: the catalog
service defines and owns the `Product` type. The cart service either depends on
a shared `catalog-api` module or defines its own `ProductRef` DTO with only the
fields it needs (`itemId`, `name`, `price`).

## Step 6: The Resulting Architecture

![CoolStore microservices architecture](/images/2026/09/coolstore-microservices-architecture.svg)

### Synchronous dependencies

Only one: **Cart -> Catalog** for product lookups. This is a single REST call
(`GET /api/products/{itemId}`) used in `ShoppingCartService.getProduct` when
adding items to the cart. It can be cached.

### Asynchronous dependencies

1. **Cart -> Order**: checkout event (`orders-out` -> `orders-in`)
2. **Order -> Catalog**: inventory deduction event (`inventory-updates`)

Both are fire-and-forget with eventual consistency.

### Database ownership

Each service owns its schema:

| Service | Tables | Former JPA entities |
|---------|--------|---------------------|
| Catalog | `CATALOG_ITEM_ENTITY`, `INVENTORY` | `CatalogItemEntity`, `InventoryEntity` |
| Cart | (in-memory or Redis) | `ShoppingCart`, `ShoppingCartItem` |
| Order | `ORDERS`, `ORDER_ITEM` | `Order`, `OrderItem` |

## Step 7: CI Guardrails for Boundary Enforcement

After the decomposition, enforce the boundaries with a policy file:

```json
{
  "forbidden_crossings": [
    ["cart", "catalog-internals"],
    ["order", "catalog-internals"],
    ["order", "cart-internals"]
  ],
  "max_impact_nodes": 20,
  "centrality_alert_threshold": 0.8
}
```

```bash
$ rgctl -r example/coolstore-weblogic -f json check --policy-file policy.json
```

This prevents re-introduction of direct cross-service calls. If a developer
adds a direct import of `CatalogService` in the order service, the policy check
fails in CI.

## What the Graph Told Me That Intuition Would Not

A developer familiar with the CoolStore would likely suggest similar service
boundaries based on domain knowledge. The graph analysis adds three things that
intuition cannot:

**1. It quantifies the cuts.** `Transformers::toProduct` has a blast radius of
40.7 with 14 nodes in the impact zone spanning two proposed services. That is
a number you can use in a design review. "This function affects 14 callers
across 2 services" is more actionable than "Transformers is used in a lot of
places."

**2. It finds hidden coupling.** The order fulfillment cluster groups `OrderServiceMDB`,
`InventoryNotificationMDB`, and `OrderService.save` by call density. Community
11250 groups the `CatalogService` inventory methods they call. This is
not obvious from the package structure -- `CatalogService` is in the `service`
package alongside cart-related EJBs, but functionally it is tightly coupled to
the order fulfillment pipeline through inventory operations. The community
detection surfaced this relationship from the call graph, not from naming
conventions.

**3. It validates the cuts are safe.** Both MDBs have blast radius 0.0. This
means converting them from JMS `@MessageDriven` beans to Reactive Messaging
`@Incoming` consumers has zero static impact on the rest of the codebase. The
graph proves the refactoring is isolated, which is exactly what you want for a
high-risk change like switching messaging infrastructure.

## When Not to Decompose

The analysis also tells you when decomposition is a bad idea. The ShoppingCart
mutations analysis showed 6 fields mutated by functions spread across 3
communities. If you tried to split `PromoService` and `ShippingService` into
separate services from the cart, every pricing operation would require
synchronous round-trips to apply promotions, calculate shipping, and update
totals. The graph coupling is too dense.

This is why communities 8064 and 4266 -- despite being separate label-propagation
clusters -- end up in one cart service. The community detection correctly
identifies distinct functional clusters at finer resolution, but the shared
mutable state (the `ShoppingCart` object) makes them inseparable at deployment
time.

## Try it out
Stop migrating by spreadsheet and tribal knowledge. If you are staring down a monolith and wondering where the hidden dependencies are, let the call graph tell you.

* **Get the tool:** Grab `rgctl` from [GitHub](https://github.com/sshaaf/rgctl).
* **Test it on your own codebase:** Navigate to your project root and run `rgctl discover . --export-migration-hints` to index your application.
* **Stop guessing:** Run `rgctl blast-radius` on your most heavily-used service and see exactly what you will break before you write a single line of code.

If `rgctl` saves you from a broken build or a doomed migration sprint, star the repository. Drop into the GitHub Discussions to share your custom agent recipes—or just to show off your most horrifying circular dependency graph.


## Commands Reference

```bash
# Build the graph with full analysis (from the rgctl repo root)
rgctl -r example/coolstore-weblogic discover . --with-cfg --with-harmonic --export-migration-hints

# List communities (natural code clusters)
rgctl -r example/coolstore-weblogic -f json gql --macro-name all_communities unused

# Inspect community members
rgctl -r example/coolstore-weblogic -f json gql \
    "MATCH (f:Function) WHERE f.community_id = '<id>' RETURN f LIMIT 25"

# Map call edges between functions
rgctl -r example/coolstore-weblogic -f json gql \
    "MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a,b LIMIT 5000"

# Check blast radius at a boundary
rgctl -r example/coolstore-weblogic -f json blast-radius <method>
rgctl -r example/coolstore-weblogic -f json blast-radius <method> --class <ClassName>
rgctl -r example/coolstore-weblogic -f json blast-radius <method> --file <ClassName>.java
rgctl -r example/coolstore-weblogic blast-radius <method>  # human-readable output

# Analyze field mutations for shared-state coupling
rgctl -r example/coolstore-weblogic -f json cpg mutations --type <ClassName> --exclude-ctors

# Enforce service boundaries in CI
rgctl -r example/coolstore-weblogic -f json check --policy-file policy.json
```
