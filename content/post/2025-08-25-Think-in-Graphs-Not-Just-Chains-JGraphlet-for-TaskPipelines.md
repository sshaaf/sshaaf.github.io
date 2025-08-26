---
title: "Think in Graphs, Not Just Chains: JGraphlet for TaskPipelines 🚀"
date: 2025-08-25
image: "/images/2025/08/jgraphlets.jpg"
tags: ["java", "async", "pipeline", "library"]
categories: ["Java", "Libraries"]
layout: post
type: post
---

**JGraphlet** is a tiny, zero-dependency library for building task pipelines in Java. Its power comes not from a long list of features, but from a small set of core design principles that work together in harmony.

At the heart of JGraphlet is simplicity, backed by a **Graph**, Add Tasks to a pipeline and connect them to create your graph. 
Each `Task` has an input and ouput, A `TaskPipeline` builds and executes a pipeline while managing the I/O for each `Task`. For example a `Map` for Fan-in, a `Record` for your own data model etc. A Taskpipeline also has a `PipelineContext` to share the data between Tasks, and furthermore Tasks can also be cached, so the computation doenst need to take place again and again. 
You can choose how your Task pipeline flow should be, and you can choose whether it should be a `SyncTask` or Async. By default all Tasks are Async.

Let's dive into the 8 core principles that define JGraphlet.
---

### 1. A Graph-First Execution Model

JGraphlet treats your workflow as a Directed Acyclic Graph (DAG). You define tasks as nodes and explicitly draw the connections (edges) between them. This makes complex patterns like fan-out (one task feeding many) and fan-in (many tasks feeding one) natural.

**Example:**

```java
import dev.shaaf.jgraphlet.*;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

try (TaskPipeline pipeline = new TaskPipeline()) {
    Task<String, String> fetchInfo = (id, ctx) -> CompletableFuture.supplyAsync(() -> "Info for " + id);
    Task<String, String> fetchFeed = (id, ctx) -> CompletableFuture.supplyAsync(() -> "Feed for " + id);
    Task<Map<String, Object>, String> combine = (inputs, ctx) -> CompletableFuture.supplyAsync(() ->
        inputs.get("infoNode") + " | " + inputs.get("feedNode")
    );

    pipeline.addTask("infoNode", fetchInfo)
            .addTask("feedNode", fetchFeed)
            .addTask("summaryNode", combine);

    pipeline.connect("infoNode", "summaryNode")
            .connect("feedNode", "summaryNode");

    String result = (String) pipeline.run("user123").join();
    System.out.println(result); // "Info for user123 | Feed for user123"
}
```

---

### 2. Two Task Styles: `Task<I,O>` and `SyncTask<I,O>`

JGraphlet provides two distinct task types you can mix and match:

- **Task<I, O> (Async):** Returns a `CompletableFuture<O>`. Perfect for I/O operations or heavy computations.
- **SyncTask<I, O> (Sync):** Returns a direct `O`. Ideal for fast, CPU-bound operations.

**Example:**

```java
try (TaskPipeline pipeline = new TaskPipeline()) {
    Task<String, String> fetchName = (userId, ctx) ->
        CompletableFuture.supplyAsync(() -> "John Doe");

    SyncTask<String, String> toUpper = (name, ctx) -> name.toUpperCase();

    pipeline.add("fetch", fetchName)
            .then("transform", toUpper);

    String result = (String) pipeline.run("user-42").join();
    System.out.println(result); // "JOHN DOE"
}
```

---

### 3. A Simple, Explicit API

JGraphlet avoids complex builders or magic configurations. The API is lean and explicit:

1. Create a pipeline: `new TaskPipeline()`
2. Register nodes: `addTask("uniqueId", task)`
3. Wire them up: `connect("fromId", "toId")`

**Example:**

```java
try (TaskPipeline pipeline = new TaskPipeline()) {
    SyncTask<String, Integer> lengthTask = (s, c) -> s.length();
    SyncTask<Integer, String> formatTask = (i, c) -> "Length is " + i;

    pipeline.addTask("calculateLength", lengthTask);
    pipeline.addTask("formatOutput", formatTask);

    pipeline.connect("calculateLength", "formatOutput");

    String result = (String) pipeline.run("Hello").join();
    System.out.println(result); // "Length is 5"
}
```

---

### 4. A Clear Fan-In Input Shape

A fan-in task receives a `Map<String, Object>`, where keys are parent task IDs and values are their results.

**Example:**

```java
try (TaskPipeline pipeline = new TaskPipeline()) {
    SyncTask<String, String> fetchUser = (id, ctx) -> "User: " + id;
    SyncTask<String, String> fetchPerms = (id, ctx) -> "Role: admin";

    Task<Map<String, Object>, String> combine = (inputs, ctx) -> CompletableFuture.supplyAsync(() -> {
        String userData = (String) inputs.get("userNode");
        String permsData = (String) inputs.get("permsNode");
        return userData + " (" + permsData + ")";
    });

    pipeline.addTask("userNode", fetchUser)
            .addTask("permsNode", fetchPerms)
            .addTask("combiner", combine);

    pipeline.connect("userNode", "combiner").connect("permsNode", "combiner");

    String result = (String) pipeline.run("user-1").join();
    System.out.println(result); // "User: user-1 (Role: admin)"
}
```

---

### 5. A Clear Run Contract

Executing a pipeline is straightforward: `pipeline.run(input)` returns a `CompletableFuture` for the final result. You can block with `.join()` or use async chaining.

**Example:**

```java
String input = "my-data";

// Blocking approach
try {
    String result = (String) pipeline.run(input).join();
    System.out.println("Result (blocking): " + result);
} catch (Exception e) {
    System.err.println("Pipeline failed: " + e.getMessage());
}

// Non-blocking approach
pipeline.run(input)
        .thenAccept(result -> System.out.println("Result (non-blocking): " + result))
        .exceptionally(ex -> {
            System.err.println("Async pipeline failed: " + ex.getMessage());
            return null;
        });
```

---

### 6. A Built-in Resource Lifecycle

JGraphlet implements `AutoCloseable`. Use try-with-resources to guarantee safe shutdown of internal resources.

**Example:**

```java
try (TaskPipeline pipeline = new TaskPipeline()) {
    pipeline.add("taskA", new SyncTask<String, String>() {
        @Override
        public String executeSync(String input, PipelineContext context) {
            if (input == null) {
                throw new IllegalArgumentException("Input cannot be null");
            }
            return "Processed: " + input;
        }
    });

    pipeline.run("data").join();

} // pipeline.shutdown() is called automatically
System.out.println("Pipeline resources have been released.");
```

---

### 7. Context

`PipelineContext` is a thread-safe, per-run workspace for metadata.

**Example:**

```java
SyncTask<String, String> taskA = (input, ctx) -> {
    ctx.put("requestID", "xyz-123");
    return input;
};
SyncTask<String, String> taskB = (input, ctx) -> {
    String reqId = ctx.get("requestID", String.class).orElse("unknown");
    return "Processed input " + input + " for request: " + reqId;
};

```

---

### 8. Optional Caching
Tasks can opt into caching to prevent re-computation.

**Example:**

```java
Task<String, String> expensiveApiCall = new Task<>() {
    @Override
    public CompletableFuture<String> execute(String input, PipelineContext context) {
        System.out.println("Performing expensive call for: " + input);
        return CompletableFuture.completedFuture("Data for " + input);
    }
    @Override
    public boolean isCacheable() { return true; }
};

try (TaskPipeline pipeline = new TaskPipeline()) {
    pipeline.add("expensive", expensiveApiCall);

    System.out.println("First call...");
    pipeline.run("same-key").join();

    System.out.println("Second call...");
    pipeline.run("same-key").join(); // Result is from cache
}
```

---

The result is a clean, testable way to orchestrate synchronous or asynchronous tasks for composing complex flows like parallel retrieval, merging, judging, and guardrails—without bringing in a heavyweight workflow engine. To learn more or try it out:

- [Maven central](https://mvnrepository.com/artifact/dev.shaaf.jgraphlet/jgraphlet)
- [Github repo](https://github.com/sshaaf/jgraphlet)

