---
title:       "Using LLMs and MCP to generate static code analysis rules"
date:        2026-03-29
image:       "/images/2026/03/using-llms-and-mcp-to-generate-static-code-analysis-rules.jpg"
tags:        ["java", "mcp", "tools"]
categories:  ["Java"]
layout: post
type: post
---

> **Scribe** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes a single tool: **`executeKantraOperation`**. That tool turns structured parameters into **YAML rules** compatible with [Konveyor](https://konveyor.io/) / [Kantra](https://github.com/konveyor/kantra)—the static analysis pipeline used for application migration and modernization. This post describes what Scribe does, how it is wired, and concrete examples you can copy.

Static code analyzers are great at what they do. Having the ability to write custom rules is important because it can cover multiple usecases such as, if an organization has their own framework or libraries that do not exist in the public domain. Or to look for patterns or anti-patterns or even best practises such as exceptions, logging etc. It can get quite cumbersome to write these rules and test them. While every conference in the world today buzzes of the word **AI**, how about we put it to real practise and provide this valuable feature with LLMs. Hence the advent of Scribe MCP server that will write Konveyor Kantra rules for an LLM. 

#### Asking the LLM to generate rules via MCP?
Here are some interesting examples of what an MCP server can help us achieve.

  1. Generate a kantra rule for me to move EntityA to EntityB annotations using scribe mcp server.
  2. write rules to convert ingress api to kubernetes gateway api. use the scribe mcp server
  3. okay then create rules to detect environment variables in a shell script. a good example is here: /getting-started/shell-script-rules/deploy.sh and stop.sh. write the rules to disk when done. 
  4. Use the following migration guide to generate Kantra rules.

This just completely changes the conversation from just simple rule generation to the user experience. As a rules developer now I have the capability to throw almost anything at the agent to build rules from. Generally speaking writing Kantra rules by hand is repetitive: every rule needs `ruleID`, `message`, `category`, `effort`, `when:` conditions (`java.referenced`, `go.referenced`, `builtin.filecontent`, `builtin.xml`, etc.), and optional `labels` / `links`. Scribe centralizes that in one MCP tool so an agent (Cursor, Claude Desktop, etc.) can generate valid rule fragments from migration guides, tickets, or ad-hoc prompts—without opening the Konveyor YAML reference every time. Furthermore, since Scribe generates rules based on a static model and not LLMs it is able to guide the LLM with the correct yaml structure. Some models have a knack for hallucination when it comes to Kantra rules as they mix up previous versions from the windup project. **`This is powerful!`**

#### A look at the rule structure
Konveyor Analyzer has the capability to analyze mutliple languages. For example it uses Java LSP to understand and analyze Java code. Where as it can also analyze C#, Python, NodeJS and Go-lang.

![flow](/images/2026/03/konveyor-analyzer-rules.jpg)

Before I go any further a brief intro about Konveyor.io a CNCF sandbox project aims at migration and modernization of applications. Its divided into multiple components that enable it to do that static code anaylsis for multiple languages. For the analyzer it requires a bunch of rules to understand what it needs to look for. These [rules](https://github.com/konveyor/rulesets) are all written in yaml. For example the following rule looks for Method calls e.g. `Thread.stop` and `Thread.destroy`.

```yaml
- category: mandatory
  customVariables: []
  description: Methods in `java.lang.Thread` have been removed
  effort: 3
  labels:
  - konveyor.io/source=openjdk8-
  - konveyor.io/source=openjdk
  - konveyor.io/target=openjdk11+
  - konveyor.io/target=openjdk
  links:
  - title: Java Thread Primitive Deprecation
    url: https://docs.oracle.com/javase/7/docs/technotes/guides/concurrency/threadPrimitiveDeprecation.html
  message: |-
    The `java.lang.Thread.stop(Throwable)` method has been removed, as it is dangerous for a thread to not only be able to directly stop another thread, but with an exception it may not expect. Instead, the thread should be notified to stop using a shared variable or `interrupt()`.
     The `java.lang.Thread.destroy()` method was never even implemented and just throws `NoSuchMethodError`.
  ruleID: java-removals-00000
  when:
    or:
    - java.referenced:
        location: METHOD_CALL
        pattern: Thread.stop(Throwable)
    - java.referenced:
        location: METHOD_CALL
        pattern: java.lang.Thread.destroy
```

### Understanding the Scribe model
> Scribe uses two MCP patterns documented in one of my previous blog [Two Essential Patterns for Building MCP Servers](https://shaaf.dev/post/2026-01-08-two-essential-patterns-for-buildingm-mcp-servers/)

![flow](/images/2026/03/scribe-model.jpg)

Lets diasect whats going on here.

1. **KantraTool** is the single Quarkus MCP `@Tool` method. It receives `operation` (a `KantraOperation` enum value) and `params` (a JSON string), then asks `CommandRegistry` for the matching `KantraCommand`.

2. **CommandRegistry** is an `@ApplicationScoped` CDI bean that discovers every `@RegisteredCommand`-annotated `KantraCommand` implementation at startup and filters them through `application.properties` (enabled/disabled lists). The result is a simple `EnumMap<KantraOperation, KantraCommand>`.

3. **KantraCommand / AbstractCommand** — the interface declares `execute(JsonNode)` and `getOperation()`. `AbstractCommand` provides shared helpers: `requireString`, `requireCategory`, `requireJavaLocation`, `buildLabels`, `buildLinks`, and `toYaml`. Concrete subclasses (one per operation group) extend it.

4. **Rule** is a Java `record` — immutable, serialized directly to YAML by Jackson. It holds all the fields Kantra needs: `ruleId`, `message`, `category`, `effort`, `labels`, `links`, and a **`Condition`**.

5. **Condition** is a sealed/polymorphic interface. Condition depends on the type of class and a when clause. For example a Java when clause could include Annotation, method call etc , or even a pattern.

| Condition class | YAML `when:` key |
|---|---|
| JavaReferencedCondition | java.referenced: |
| GoReferencedCondition | go.referenced: |
| GoDependencyCondition | go.dependency: |
| BuiltinFileContentCondition | builtin.filecontent: |
| BuiltinXmlCondition | builtin.xml: |
| BuiltinJsonCondition | builtin.json: |
| AndCondition / OrCondition | and: / or: |

`JavaReferencedCondition` carries a `JavaLocation` enum (IMPORT, ANNOTATION, INHERITANCE, METHOD_CALL, etc.) which Kantra's Java provider uses to scope its AST search precisely — that is why a rule with `location: ANNOTATION` fires only on `@Foo` usages and not on a plain import or type reference.

---

### Example 1: Java import migration

**Goal:** Flag imports `com.opensymphony.xwork2`
**MCP call (conceptual):**

- `operation`: `CREATE_JAVA_CLASS_RULE`
- `params` (JSON string):

```yaml
- ruleID: "struts6-to-7-001"
  description: "Detects Java import com.opensymphony.xwork2"
  message: |
    ## Before

    Imports from `com.opensymphony.xwork2` (XWork2).

    ## After

    Struts 7 migrates XWork2 to `org.apache.struts2`. Replace package `com.opensymphony.xwork2` with `org.apache.struts2`. Same for `org.opensymphony.xwork2`.

    ## Additional info

    - Simple search/replace for package renames.
    - See migration guide for per-class mapping (Action, TextProvider, etc.).
  category: "mandatory"
  effort: 2
  labels:
    - "konveyor.io/source=struts6"
    - "konveyor.io/target=struts7"
  links:
    - title: "Struts 6 to 7 migration"
      url: "https://cwiki.apache.org/confluence/display/WW/Struts+6.x.x+to+7.x.x+migration"
  when:
    java.referenced:
      pattern: "com.opensymphony.xwork2"
      location: "IMPORT"
```

You then merge this into your ruleset or run `VALIDATE_RULE` with the YAML if exposed. Rule validation is a basic validation of yaml only.

---

### Example 2: Go type reference (Kubernetes Ingress → Gateway API)

**Goal:** Surface code that references `Ingress` so teams can move toward `HTTPRoute`.

- `operation`: `CREATE_GO_REFERENCED_RULE`
- `params`:

```yaml
- ruleID: "ingress-nginx-go-ref-00002"
  description: "Detects IngressClass type usage"
  message: |
    This code references `networkingv1.IngressClass`. Migrate to `gatewayv1.GatewayClass`.

    **Migration:**

    ```go
    // Before
    ingressClass := &networkingv1.IngressClass{...}

    // After
    gatewayClass := &gatewayv1.GatewayClass{...}
    ```
  category: "mandatory"
  effort: 3
  labels:
    - "konveyor.io/source=ingress-nginx"
    - "konveyor.io/target=gateway-api"
  when:
    go.referenced:
      pattern: 'IngressClass'
```


---

### Example 3: File content + XML (Struts / `struts.xml`)

**File content** — match a substring in Go/Java/XML templates:

- `operation`: `CREATE_FILE_CONTENT_RULE`
- `params`:

```yaml
- ruleID: "struts6-to-7-008"
  description: "XML interceptor-ref fileUpload → actionFileUpload"
  message: |
    ## Before

    struts.xml references fileUpload interceptor.

    ## After

    Change to actionFileUpload. Use `<interceptor-ref name="actionFileUpload"/>`.

    ## Additional info

    - Action File Upload Interceptor replaces the removed interceptor.
  category: "mandatory"
  effort: 1
  labels:
    - "konveyor.io/source=struts6"
    - "konveyor.io/target=struts7"
  when:
    builtin.xml:
      xpath: "//interceptor-ref[@name=\"fileUpload\"]"
```

---

### Running and connecting

For more details on installation of downloading visit the [project README](https://github.com/sshaaf/scribe)

**Cursor / VS Code** (`mcp.json`):

```json
{
  "mcpServers": {
    "scribe": {
      "url": "http://localhost:8080/mcp/sse"
    }
  }
}
```

The LLM sees `executeKantraOperation` in the tool list; it does not need to read Scribe’s Java sources to use it—the `@Tool` / `@ToolArg` descriptions carry the parameter schema.

---

### Limitations (explicit)

Its important that I also mention the limitations. 

- Scribe **generates** rule YAML; it does **not** run Kantra against your repo.
- **Message quality** still matters: richer Before/After markdown improves downstream use (e.g. Konveyor AI / fix hints).
- **JSON in `params`:** must be a single JSON object string; newlines inside strings must be escaped as `\n` when wrapped by another JSON serializer.
- **Noise vs. precision:** Broad `builtin.filecontent` patterns (e.g. short substrings) produce false positives; narrow patterns or `java.referenced` / `go.referenced` are usually safer.

---

## Summary

Scribe is a small MCP façade over a registry of rule generators: one tool, many operations, YAML out. Use it when you want agents or IDE integrations to produce Konveyor-compatible rules quickly, with optional locking down of which operations are enabled in production deployments. I am not planning to stop there, I would definitely like to bring more value to add [openrewrite](https://github.com/openrewrite) recipies and [semgrep](https://semgrep.dev/) rules.

**References**

- [Konveyor](https://konveyor.io/)
- [Kantra](https://github.com/konveyor/kantra)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Scribe repository](https://github.com/sshaaf/scribe)
