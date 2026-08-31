---
title:       "Migrating an application to Quarkus: A Graph-Driven Approach with rgctl"
subtitle:    "Using call-graph analysis to make migration decisions based on structural data"
description: "A step-by-step walkthrough of migrating a Java EE 7 CoolStore monolith from WebLogic to Quarkus, using rgctl's blast radius, community detection, and migration planning to replace guesswork with graph-driven evidence."
date:        2026-08-31
image:       "/images/2026/08/migrating-coolstore-to-quarkus-with-rgctl.jpg"
tags:        ["java", "quarkus", "migration", "rgctl", "call-graph"]
categories:  ["Modernization"]
layout: post
type: post
devto: true
---
Migrating an application takes a lot of time and energy, which itself is on a collision course
with complexity in codebases. Leaving aside the discussion on people and process. In this blog post
I would like to highlight the journey of migrating and using a tool like [rgctl](https://github.com/sshaaf/rgctl) which understands the codebase, 
from a Graph POV and also understands its semnatically. It isnt a community detector only but puts emphasis on
mining the code details via Call graphs, dependenices, data flow in code, slicing, blast radius, harmonic centrality, betweeness and a little more of those things 😎.
rgctl takes one more step forward, using centraility, cfg etc, it creates migration hints. So one can choose the different ways to migrate and application.


A common question in application modernization is "where do I start?" You have a
monolith with dozens of tightly-coupled EJBs, JMS resources, JNDI lookups, and
vendor-specific descriptors. You need to get it onto Quarkus. The traditional
answer is a spreadsheet, tribal knowledge, and hope. This post walks through a
different approach: using static call-graph analysis to make migration decisions
based on structural data rather than guesswork.

I'll use [rgctl](https://github.com/sshaaf/rgctl) to analyze a real
Java EE 7 application -- the CoolStore monolith -- and walk through the entire
migration from WebLogic to Quarkus, step by step, with actual tool output at
each stage.

## The Application: CoolStore on WebLogic

The CoolStore is a Java EE 7 e-commerce application packaged as a WAR and
deployed on Oracle WebLogic Server 12.2.1.4. It has 25 Java classes across 5
packages:

```bash
com.redhat.coolstore/
  model/          8 classes   JPA entities and DTOs
  service/        9 classes   EJB business logic + MDBs
  rest/           4 classes   JAX-RS endpoints
  persistence/    1 class     CDI EntityManager producer
  utils/          3 classes   Logger producer, startup hook, transformers
```

The architecture follows a standard Java EE layered pattern:

```bash
Browser -> AngularJS SPA
             |
        JAX-RS /services/*
             |
    CartEndpoint    ProductEndpoint    OrderEndpoint
    @SessionScoped  @RequestScoped     @RequestScoped
             |              |               |
    ShoppingCart-    ProductService    OrderService
    Service         @Stateless        @Stateless
    @Stateful            |
         |          CatalogService
         |          @Stateless
         |               |
         +---> ShippingService @Remote (JNDI lookup)
         |
         +---> PromoService @ApplicationScoped
         |
         +---> ShoppingCartOrderProcessor @Stateless
                       |
                  JMS Topic (jms/topic/orders)
                       |
              +--------+--------+
              |                 |
        OrderServiceMDB    InventoryNotificationMDB
        (persist order)    (low-stock alerts)
```

The Java EE APIs in use that need migration work:

- **EJB**: 5 `@Stateless`, 1 `@Stateful`, 1 `@Singleton`, 2 `@MessageDriven`
- **JMS**: `ConnectionFactory` + `Topic` via `@Resource(lookup=...)`, 2 MDB consumers
- **JNDI**: `InitialContext.lookup("ejb/ShippingService")` for `@Remote` EJB
- **JPA**: EclipseLink provider, `@PersistenceContext`, 4 entity classes
- **JAX-RS**: 3 resource endpoints + `@ApplicationPath` activator
- **WebLogic-specific**: `weblogic.xml`, `weblogic-ejb-jar.xml`, WLST scripts

## Phase 1: Build the Call Graph

The first step is to index the codebase. rgctl's `discover` command parses
source files, builds the function-level call graph, computes centrality metrics,
detects communities, and pre-computes blast radius for every function:

```bash
$ rgctl discover example/coolstore-weblogic \
    --with-cfg \
    --with-harmonic \
    --with-security \
    --export-migration-hints \
    --migration-preset risk_mitigation
```

```bash
[>] rgctl discover
[!] Deep analysis enabled (--with-cfg / --with-taint).
[✓] Indexed 1226 files -> 14760 nodes, 50082 edges
Skipped files due to errors: 1
[✓] Analyzed 7526 functions (avg complexity: 1.0)
[✓] Detected 10870 communities (modularity: 0.30)
[!] Found 186 circular dependencies

✓ Security analysis:
  Potential secrets found: 5

✓ Control flow analysis:
  Field writes indexed: 3299
  CFG/PDG/Dominance: 6585 functions analyzed
  Skipped: 941 functions (unsupported language or parse error)

[✓] Migration plan (Risk Mitigation): 152 steps
[✓] rgctl discover finished in 22.7s
```

A few things to note:

- **186 circular dependencies** -- this is normal for a Java EE monolith where
  EJBs freely inject each other. It is exactly the kind of coupling that makes
  migration ordering hard without tooling.
- **5 potential secrets** -- the security scan flagged hardcoded values. In a
  real migration, you would rotate these before they end up in a Quarkus
  `application.properties`.
- **6585 functions analyzed** -- the project includes bower_components (the
  AngularJS frontend), so the graph covers both Java and JavaScript. For
  migration purposes, I focus on the Java side, but the cross-language call
  edges (REST endpoint -> JS controller) are real and show up in blast radius.

The result is a `.rgctl/` directory with the graph snapshot, blast engine
index, and a `migration_plan.json`.

## Phase 2: Inventory the Codebase

Before planning, I need to understand what I have. Query the graph for all
Java classes:

```bash
$ rgctl -f json gql "MATCH (c:Class) RETURN c" 2>/dev/null \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for row in data['rows']:
    for item in row:
        if '.java' in item.get('file',''):
            print(f'{item[\"node\"]:40s} {item[\"qualified_name\"]}')" \
  | sort
```

```bash
CartEndpoint                             com.redhat.coolstore.rest.CartEndpoint
CatalogItemEntity                        com.redhat.coolstore.model.CatalogItemEntity
CatalogService                           com.redhat.coolstore.service.CatalogService
InventoryEntity                          com.redhat.coolstore.model.InventoryEntity
InventoryNotificationMDB                 com.redhat.coolstore.service.InventoryNotificationMDB
Order                                    com.redhat.coolstore.model.Order
OrderEndpoint                            com.redhat.coolstore.rest.OrderEndpoint
OrderItem                                com.redhat.coolstore.model.OrderItem
OrderService                             com.redhat.coolstore.service.OrderService
OrderServiceMDB                          com.redhat.coolstore.service.OrderServiceMDB
Producers                                com.redhat.coolstore.utils.Producers
Product                                  com.redhat.coolstore.model.Product
ProductEndpoint                          com.redhat.coolstore.rest.ProductEndpoint
ProductService                           com.redhat.coolstore.service.ProductService
Promotion                                com.redhat.coolstore.model.Promotion
PromoService                             com.redhat.coolstore.service.PromoService
Resources                                com.redhat.coolstore.persistence.Resources
RestApplication                          com.redhat.coolstore.rest.RestApplication
ShippingService                          com.redhat.coolstore.service.ShippingService
ShoppingCart                             com.redhat.coolstore.model.ShoppingCart
ShoppingCartItem                         com.redhat.coolstore.model.ShoppingCartItem
ShoppingCartOrderProcessor               com.redhat.coolstore.service.ShoppingCartOrderProcessor
ShoppingCartService                      com.redhat.coolstore.service.ShoppingCartService
StartupListener                          com.redhat.coolstore.utils.StartupListener
Transformers                             com.redhat.coolstore.utils.Transformers
```

25 classes. Every one I need to touch is here.

## Phase 3: Understand Risk with Blast Radius

Blast radius answers a specific question: **"if I change this function, what
breaks upstream?"** It uses pre-computed SCC (Strongly Connected Component)
decomposition of the call graph to identify all transitive callers of a given
symbol. The result is an impact score from 0 to 100, the list of direct callers,
and the full impact zone.

This is the most operationally useful tool for migration ordering. Let's run it
on the riskiest-looking class first -- `ShoppingCartService`:

```bash
$ rgctl -r example/coolstore-weblogic blast-radius getShoppingCart
```

```bash
Blast radius for 'getShoppingCart'
  Score: 40.5/100
  Direct callers: 6
  Impact zone: 10
  Callers: ShoppingCartService.checkOutShoppingCart,
           CartEndpoint.add,
           CartEndpoint.dedupeCartItems,
           CartEndpoint.delete,
           CartEndpoint.getCart,
           CartEndpoint.set
  Impact:  CartEndpoint.getCart,
           CartEndpoint.add,
           CartEndpoint.set,
           CartEndpoint.delete,
           CartEndpoint.dedupeCartItems,
           CartEndpoint.checkout,
           ShoppingCartService.checkOutShoppingCart,
           reset (controllers.js),
           performAction (controllers.js),
           anonymous (controllers.js)
```

A score of 40.5 with 10 nodes in the impact zone. Change `getShoppingCart` and
you potentially affect 6 Java methods plus 3 JavaScript controller functions.
That is a lot of surface area -- this is not where you want to start your
migration.

Now look at the JSON output for more detail:

```bash
$ rgctl -r example/coolstore-weblogic -f json blast-radius getShoppingCart
```

```json
{
  "schema_version": 2,
  "target": {
    "canonical_fqn": "ShoppingCartService::getShoppingCart",
    "class_context": "ShoppingCartService",
    "file_path": ".../service/ShoppingCartService.java",
    "language": "java",
    "signature": "public ShoppingCart getShoppingCart(String cartId) {"
  },
  "metrics": {
    "score": 40.5,
    "direct_callers_count": 6,
    "impact_zone_size": 10
  },
  "topology": {
    "scc_component_id": 580,
    "direct_callers": [
      {"fqn": "com.redhat.coolstore.service.ShoppingCartService.checkOutShoppingCart"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.add"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.dedupeCartItems"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.delete"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.getCart"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.set"}
    ],
    "impact_zone": ["...10 entries..."]
  },
  "gatekeeping": {
    "policy_status": "SKIPPED"
  }
}
```

The `scc_component_id: 580` tells me this function is part of a strongly
connected component in the call graph -- there are cycles (which matches the 186
circular dependencies the discover phase reported).

Let's compare with a simpler function:

```bash
$ rgctl -r example/coolstore-weblogic -f json blast-radius calculateShipping \
    --file ShippingService.java
```

```json
{
  "target": {
    "canonical_fqn": "ShippingService::calculateShipping",
    "class_context": "ShippingService"
  },
  "metrics": {
    "score": 0.0,
    "direct_callers_count": 0,
    "impact_zone_size": 0
  }
}
```

Score of 0.0. Zero direct callers in the static graph. `ShippingService` is
called via JNDI lookup (`InitialContext.lookup("ejb/ShippingService")`), which
is a runtime dispatch that static analysis cannot resolve. This is actually
useful information: it tells me this class is structurally isolated. I can
migrate it safely without breaking any statically-visible call paths.

A few more blast radius checks to build the full picture:

| Symbol | Score | Direct Callers | Impact Zone |
|--------|-------|----------------|-------------|
| `ShoppingCartService::`<br>`getShoppingCart` | 40.5 | 6 | 10 |
| `ShoppingCartService::`<br>`priceShoppingCart` | 40.4 | 5 | 7 |
| `ShoppingCartService::`<br>`checkOutShoppingCart` | 25.1 | 1 | 2 |
| `ProductService::`<br>`getProducts` | 40.1 | 2 | 2 |
| `PromoService::`<br>`applyCartItemPromotions` | 25.4 | 1 | 8 |
| `CatalogService::`<br>`getCatalogItems` | 25.1 | 1 | 3 |
| `OrderService::`<br>`getOrders` | 25.1 | 1 | 1 |
| `CartEndpoint::`<br>`checkout` | 25.1 | 1 | 1 |
| `OrderServiceMDB::`<br>`onMessage` | 0.0 | 0 | 0 |
| `ShippingService::`<br>`calculateShipping` | 0.0 | 0 | 0 |

The pattern is clear: the `ShoppingCartService` methods have the highest blast
radius because everything flows through the cart. The MDBs and
`ShippingService` have zero because they are invoked through JMS and JNDI
respectively -- runtime dispatch, not static calls.

## Phase 4: Read the Migration Plan

The `--export-migration-hints` flag during discover produced a
`migration_plan.json`. This is a package-level roadmap that combines three
signals into a priority score:

- **PageRank (alpha)** -- how central the package is in the call graph
- **Harmonic centrality (beta)** -- how reachable the package is from all others
- **Max blast radius (gamma)** -- the worst-case impact of changing anything in the package

The priority formula:

```bash
Priority(p) = alpha * norm(pagerank) + beta * norm(harmonic) - gamma * norm(max_blast)
```

I used `--migration-preset risk_mitigation`, which sets `gamma = 0.70` --
heavily penalizing high-blast packages. This means the plan orders safe,
low-impact packages first.

```bash
$ cat .rgctl/migration_plan.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for s in data['steps']:
    if 'redhat' in s['label']:
        print(f'Step {s[\"step\"]:3d} | schedule:{s[\"schedule_step\"]:3d} '
              f'| rank:{s[\"priority_rank\"]:3d} '
              f'| score:{s[\"priority_score\"]:+.4f} | {s[\"label\"]}')"
```

```bash
Step   2 | schedule:  2 | rank: 72 | score:-0.3424 | com.redhat.coolstore.model
Step  49 | schedule: 49 | rank:127 | score:-0.3500 | com.redhat.coolstore.persistence
Step  76 | schedule: 76 | rank:  2 | score:-0.1801 | com.redhat.coolstore.rest
Step  84 | schedule: 84 | rank: 10 | score:-0.2695 | com.redhat.coolstore.utils
Step  87 | schedule: 87 | rank: 13 | score:-0.2791 | com.redhat.coolstore.service
```

The `schedule_step` column is a dependency-aware topological sort (Kahn's
algorithm on the package call graph): packages that are called by others come
first. The `priority_rank` column is pure score ranking.

Reading this:

1. **`com.redhat.coolstore.model`** (step 2) -- migrate first. These are JPA
   entities and POJOs. They sit at the bottom of the dependency chain and
   nothing else breaks when you change them.
2. **`com.redhat.coolstore.persistence`** (step 49) -- the `Resources` CDI
   producer for `EntityManager`. Small, isolated.
3. **`com.redhat.coolstore.rest`** (step 76) -- the REST endpoints. They sit at
   the top of the call chain (rank 2 by priority, meaning high harmonic
   centrality) but depend on everything below.
4. **`com.redhat.coolstore.utils`** (step 84) -- utility classes.
5. **`com.redhat.coolstore.service`** (step 87) -- the EJB layer. Migrated last
   because it has the most complexity (stateful beans, JMS, JNDI) and the
   highest aggregate blast radius.

This ordering matches engineering intuition, but it was derived from the graph
structure, not from guessing.

## Phase 5: Execute the Migration

With the analysis done, I migrate package by package following the plan. Below
is the concrete work for each phase.

### Step 1: Entities and DTOs (`com.redhat.coolstore.model`)

The model classes need three changes:

1. **Namespace**: `javax.persistence.*` -> `jakarta.persistence.*`
2. **Drop JAXB**: Remove `@XmlRootElement` from `InventoryEntity` (Quarkus uses
   Jackson by default)
3. **JPA provider**: Switch from EclipseLink to Hibernate ORM (Quarkus default)

Before (`CatalogItemEntity.java`):
```java
import javax.persistence.Entity;
import javax.persistence.Table;
// ...
```

After:
```java
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
// ...
```

The `ShoppingCart` class is annotated `@Dependent` (CDI). In Quarkus, this
continues to work as-is after the namespace change.

Delete `persistence.xml` entirely. Replace with `application.properties`:

```properties
quarkus.datasource.db-kind=h2
quarkus.datasource.jdbc.url=jdbc:h2:mem:coolstore;DB_CLOSE_DELAY=-1
quarkus.hibernate-orm.database.generation=drop-and-create
quarkus.hibernate-orm.sql-load-script=import.sql
```

This is safe. Blast radius for the model classes is low -- they are callees, not
callers.

### Step 2: Persistence Producer (`com.redhat.coolstore.persistence`)

The `Resources` class produces an `EntityManager` via `@PersistenceContext`:

```java
// Before
@PersistenceContext
@Produces
private EntityManager em;
```

In Quarkus, you do not need a CDI producer for `EntityManager`. Quarkus injects
it directly. Remove the `Resources` class entirely and inject `EntityManager`
where needed:

```java
// After (in service classes)
@Inject
EntityManager em;
```

### Step 3: Utilities (`com.redhat.coolstore.utils`)

**`Producers.java`** -- The `Logger` CDI producer works in Quarkus after
`javax` -> `jakarta` namespace changes. Alternatively, Quarkus provides built-in
logging via `@Inject Logger` or the `jboss-logging` API.

**`StartupListener.java`** -- This is an EJB `@Singleton` + `@Startup`:

```java
// Before
@Singleton
@Startup
public class StartupListener {
    @PostConstruct
    public void onStartup() {
        log.info("CoolStore Application Started");
    }
}
```

Replace with Quarkus CDI lifecycle event:

```java
// After
@ApplicationScoped
public class StartupListener {
    void onStartup(@Observes StartupEvent event) {
        Log.info("CoolStore Application Started");
    }
}
```

**`Transformers.java`** -- Uses `javax.json.*` (JSON-P) for manual JSON
building. In Quarkus, replace with Jackson `ObjectMapper` or keep JSON-P with
the `quarkus-jsonp` extension. Either works; Jackson is the path of least
resistance since Quarkus RESTEasy uses it by default.

### Step 4: ShippingService (low-risk EJB extraction)

Blast radius: **0.0**. This is the ideal first EJB to migrate.

Before:
```java
@Stateless
@Remote
public class ShippingService implements ShippingServiceRemote {
    @Override
    public double calculateShipping(ShoppingCart sc) {
        // price-based shipping tiers
    }
}
```

After:
```java
@ApplicationScoped
public class ShippingService {
    public double calculateShipping(ShoppingCart sc) {
        // same logic, no EJB, no @Remote
    }
}
```

Remove the `ShippingServiceRemote` interface entirely. Remove the JNDI lookup
in `ShoppingCartService`:

```java
// Before (ShoppingCartService.java line 114-122)
private static ShippingServiceRemote lookupShippingServiceRemote() {
    try {
        final Context context = new InitialContext();
        return (ShippingServiceRemote) context.lookup("ejb/ShippingService");
    } catch (NamingException e) {
        throw new RuntimeException(e);
    }
}
```

Replace with CDI injection:

```java
// After
@Inject
ShippingService shippingService;

// In priceShoppingCart(), replace:
//   lookupShippingServiceRemote().calculateShipping(sc)
// with:
//   shippingService.calculateShipping(sc)
```

This eliminates the JNDI dependency, the `@Remote` interface, and the
`weblogic.xml` JNDI binding for `ejb/ShippingService`.

### Step 5: Stateless EJBs (CatalogService, OrderService, ProductService, PromoService)

These all follow the same pattern. Take `CatalogService`:

Before:
```java
@Stateless
public class CatalogService {
    @Inject
    private EntityManager em;

    public List<CatalogItemEntity> getCatalogItems() {
        CriteriaBuilder cb = em.getCriteriaBuilder();
        CriteriaQuery<CatalogItemEntity> criteria = cb.createQuery(CatalogItemEntity.class);
        Root<CatalogItemEntity> member = criteria.from(CatalogItemEntity.class);
        criteria.select(member);
        return em.createQuery(criteria).getResultList();
    }
}
```

After:
```java
@ApplicationScoped
@Transactional
public class CatalogService {
    @Inject
    EntityManager em;

    public List<CatalogItemEntity> getCatalogItems() {
        // Same JPA logic -- works identically on Hibernate
    }
}
```

The change: `@Stateless` -> `@ApplicationScoped` + `@Transactional`. The JPA
code remains the same. Quarkus's Hibernate ORM handles the EntityManager
lifecycle.

Blast radius for `CatalogService::getCatalogItems` is 25.1 (1 direct caller:
`ProductService.getProducts`, which propagates to `ProductEndpoint.listAll`).
Moderate risk, but manageable because the callers are simple pass-through methods.

Apply the same pattern to `OrderService`, `ProductService`, and `PromoService`.

### Step 6: ShoppingCartOrderProcessor (JMS producer)

This is the most involved single-class change. The original uses WebLogic JMS
resources injected via JNDI:

```java
@Stateless
public class ShoppingCartOrderProcessor {
    @Resource(lookup = "weblogic.jms.ConnectionFactory")
    private ConnectionFactory connectionFactory;

    @Resource(lookup = "jms/topic/orders")
    private Topic ordersTopic;

    public void process(ShoppingCart cart) {
        try (JMSContext context = connectionFactory.createContext()) {
            context.createProducer().send(ordersTopic,
                Transformers.shoppingCartToJson(cart));
        }
    }
}
```

Two options for Quarkus:

**Option A: SmallRye Reactive Messaging (recommended)**

```java
@ApplicationScoped
public class ShoppingCartOrderProcessor {
    @Inject
    @Channel("orders")
    Emitter<String> ordersEmitter;

    public void process(ShoppingCart cart) {
        ordersEmitter.send(Transformers.shoppingCartToJson(cart));
    }
}
```

With `application.properties`:
```properties
mp.messaging.outgoing.orders.connector=smallrye-in-memory
# or for Kafka: smallrye-kafka
# or for AMQP: smallrye-amqp
```

**Option B: Quarkus Artemis JMS** (if you want to keep JMS semantics):
```java
@ApplicationScoped
public class ShoppingCartOrderProcessor {
    @Inject
    ConnectionFactory connectionFactory;

    public void process(ShoppingCart cart) {
        try (JMSContext context = connectionFactory.createContext()) {
            context.createProducer().send(
                context.createTopic("orders"),
                Transformers.shoppingCartToJson(cart));
        }
    }
}
```

### Step 7: Message-Driven Beans (OrderServiceMDB, InventoryNotificationMDB)

Both MDBs have blast radius of 0.0 (they are entry points, invoked by the
messaging runtime, not by application code). But they depend on services
migrated in earlier steps, so they must come after.

**OrderServiceMDB** -- before:
```java
@MessageDriven(name = "OrderServiceMDB", activationConfig = {
    @ActivationConfigProperty(propertyName = "destinationLookup",
                              propertyValue = "topic/orders"),
    @ActivationConfigProperty(propertyName = "destinationType",
                              propertyValue = "javax.jms.Topic"),
    @ActivationConfigProperty(propertyName = "acknowledgeMode",
                              propertyValue = "Auto-acknowledge")})
public class OrderServiceMDB implements MessageListener {
    @Inject OrderService orderService;
    @Inject CatalogService catalogService;

    @Override
    public void onMessage(Message rcvMessage) {
        TextMessage msg = (TextMessage) rcvMessage;
        String orderStr = msg.getBody(String.class);
        Order order = Transformers.jsonToOrder(orderStr);
        orderService.save(order);
        order.getItemList().forEach(orderItem -> {
            catalogService.updateInventoryItems(
                orderItem.getProductId(), orderItem.getQuantity());
        });
    }
}
```

After (SmallRye Reactive Messaging):
```java
@ApplicationScoped
public class OrderServiceMDB {
    @Inject OrderService orderService;
    @Inject CatalogService catalogService;

    @Incoming("orders")
    public void onMessage(String orderStr) {
        Order order = Transformers.jsonToOrder(orderStr);
        orderService.save(order);
        order.getItemList().forEach(orderItem -> {
            catalogService.updateInventoryItems(
                orderItem.getProductId(), orderItem.getQuantity());
        });
    }
}
```

The `@MessageDriven` annotation, `MessageListener` interface,
`ActivationConfigProperty` array, and JMS `Message` unwrapping are all gone.
The method now takes a `String` directly from the channel.

Apply the same pattern to `InventoryNotificationMDB`.

### Step 8: ShoppingCartService (the hard one)

This is the highest-risk class: blast radius of 40.5 for `getShoppingCart`,
40.4 for `priceShoppingCart`. It has three problems:

1. **`@Stateful` EJB** -- holds a `ShoppingCart` instance in memory per session
2. **JNDI lookup** -- `InitialContext.lookup("ejb/ShippingService")`
3. **Injects other EJBs** -- `ProductService`, `PromoService`,
   `ShoppingCartOrderProcessor`

The JNDI lookup was already eliminated in Step 4. The other EJBs were migrated
to CDI beans in Steps 5-6. What remains is the stateful nature.

Before:
```java
@Stateful
public class ShoppingCartService {
    private ShoppingCart cart = new ShoppingCart();

    public ShoppingCart getShoppingCart(String cartId) {
        return cart;
    }
    // ...
}
```

Quarkus has no EJB container, so `@Stateful` does not exist. The cart state
needs to go somewhere. For a monolith migration, the simplest option is
`@ApplicationScoped` with a `ConcurrentHashMap`:

```java
@ApplicationScoped
public class ShoppingCartService {
    private final ConcurrentHashMap<String, ShoppingCart> carts = new ConcurrentHashMap<>();

    public ShoppingCart getShoppingCart(String cartId) {
        return carts.computeIfAbsent(cartId, k -> new ShoppingCart());
    }
    // ...
}
```

For production use, back this with Redis or a database. But for a migration
that preserves behavior, the in-memory map is functionally equivalent.

### Step 9: REST Endpoints

The JAX-RS endpoints need:

1. `javax.ws.rs.*` -> `jakarta.ws.rs.*`
2. Remove `RestApplication.java` (Quarkus auto-discovers JAX-RS resources)
3. Fix `CartEndpoint`'s `@SessionScoped` -- Quarkus does not support
   `@SessionScoped` for REST endpoints by default

`CartEndpoint` before:
```java
@SessionScoped
@Path("/cart")
public class CartEndpoint implements Serializable {
    @Inject
    private ShoppingCartService shoppingCartService;
    // ...
}
```

After:
```java
@RequestScoped
@Path("/cart")
public class CartEndpoint {
    @Inject
    ShoppingCartService shoppingCartService;
    // ...
}
```

Since `ShoppingCartService` now manages cart state by ID (the `ConcurrentHashMap`
approach), the endpoint no longer needs to be `@SessionScoped`.

### Step 10: WebLogic Descriptors

Delete:
- `WEB-INF/weblogic.xml` -- JNDI mappings, session replication config,
  classloader preferences. None apply to Quarkus.
- `WEB-INF/weblogic-ejb-jar.xml` -- EJB pool sizes, stateful cache/clustering,
  MDB destination bindings. None apply.
- `weblogic-config/*.py` -- WLST domain creation scripts.
- `docker-compose.yml` -- WebLogic container definition.

Replace `persistence.xml` with `application.properties` (done in Step 1).

### Step 11: Frontend

The JSP files (`index.jsp`, `health.jsp`) do not work in Quarkus. Move the
AngularJS SPA to `src/main/resources/META-INF/resources/` and serve as static
files. Replace `health.jsp` with the Quarkus SmallRye Health extension:

```properties
# pom.xml dependency
quarkus-smallrye-health
# exposes /q/health automatically
```

## Phase 6: CI Guardrails

After the migration, set up policy checks to prevent regressions. Write a
`policy.json`:

```json
{
  "max_impact_nodes": 15,
  "centrality_alert_threshold": 0.8
}
```

Gate PRs in CI:

```bash
$ rgctl discover . --with-cfg --with-harmonic --export-migration-hints
$ rgctl -f json check --policy-file policy.json
```

If any changed function has a blast radius exceeding 15 impact nodes, or if the
impact zone crosses a high-betweenness bridge node, the check exits with code 1
and the PR fails. This is useful during the migration itself to catch accidental
scope creep -- changing a "safe" class that inadvertently pulls in a high-blast
dependency.

## Summary

The migration order derived from the call graph analysis:

| Step | Package/Class | Blast Radius | Change |
|------|---------------|-------------|--------|
| 1 | `model/*` (entities, DTOs) | Low | `javax` -> `jakarta` namespace |
| 2 | `persistence/Resources` | 0.0 | Delete (Quarkus injects EntityManager) |
| 3 | `utils/*` | Low | `@Singleton @Startup` -> `@Observes StartupEvent` |
| 4 | `ShippingService` | 0.0 | Drop `@Remote`, `@Stateless` -> `@ApplicationScoped`, delete JNDI lookup |
| 5 | `CatalogService`, `OrderService`, `ProductService`, `PromoService` | 25.1 | `@Stateless` -> `@ApplicationScoped @Transactional` |
| 6 | `ShoppingCartOrderProcessor` | Moderate | JMS `@Resource` -> SmallRye Reactive Messaging `@Channel` |
| 7 | `OrderServiceMDB`, `InventoryNotificationMDB` | 0.0 | `@MessageDriven` -> `@Incoming` |
| 8 | `ShoppingCartService` | 40.5 | `@Stateful` -> `@ApplicationScoped` + external state |
| 9 | REST endpoints | 25.1 | `@SessionScoped` -> `@RequestScoped`, remove `RestApplication` |
| 10 | WebLogic descriptors | -- | Delete `weblogic.xml`, `weblogic-ejb-jar.xml` |
| 11 | Frontend | -- | JSP -> static files, add SmallRye Health |

The key insight is not that this ordering is surprising -- an experienced Java
EE developer would likely arrive at a similar sequence. The point is that the
call graph provides **structural evidence** for migration decisions. When you are
working on a codebase you do not know well, or one with 500 classes instead of
25, the blast radius numbers replace guesswork with data. A score of 40.5 means
something concrete: 6 direct callers and 10 transitive dependents. That is the
scope of what needs testing after you touch that method.

The migration plan's topological sort also catches dependency ordering mistakes
that are easy to make manually. You cannot migrate `ShoppingCartService` before
`ShippingService` because the JNDI lookup replacement requires `ShippingService`
to already be a CDI bean. The plan encodes this constraint automatically.

For larger codebases -- hundreds of EJBs, nested module dependencies, shared
libraries -- this kind of structural analysis scales where spreadsheets do not.

## Commands Reference

```bash
# Index the codebase
rgctl discover <path> \
  --with-cfg --with-harmonic --with-security \
  --export-migration-hints --migration-preset risk_mitigation

# List all classes
rgctl -f json gql "MATCH (c:Class) RETURN c"

# Check blast radius for a method
rgctl -f json blast-radius <method>
rgctl -f json blast-radius <method> --file <ClassName>.java
rgctl blast-radius <method>  # human-readable output

# Read the migration plan
cat .rgctl/migration_plan.json

# CI policy check
rgctl -f json check --policy-file policy.json

# List communities (natural code clusters)
rgctl -f json gql --macro-name all_communities unused

# Centrality metrics
rgctl -f json metrics --pagerank
```
