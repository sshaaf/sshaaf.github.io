---
title:       "Nano Agent, Mega Senses: Adding LSP to the 260-Line Coding Agent"
date:        2026-04-08
image:       "/images/2026/04/nanocode-java.jpg"
tags:        ["java", "llm", "tools"]
categories:  ["Java"]
layout: post
type: post
devto: true
---

Learn, learn, and learn more—that’s the name of the game. Coding agents are innovating fast; things are getting bigger and, quite often, bloated. To understand what an agent is actually doing, I’ve found it’s best to go back to the basics. It takes a bit more time, but the expertise you gain along the way sets you up for the long haul." So here I read [Max's](https://xam.dk/blog/nanocode-coding-agent-in-260-lines-of-java/) post and thought, how about add some more things to this. Fetching ideas... done.. Lets add LSP support. 

The original [nanocode](https://github.com/1rgs/nanocode) idea is easy to lose in the hype: **a coding agent is mostly a loop**. You send prompt plus tool definitions to the model; the model answers with text or tool calls; you execute tools, feed results back, and repeat. The heavy lifting is the model; your code is **hands** (write, edit, shell) and **eyes** (read, glob, grep).

That pattern is how “real” agents are structured too — usually with more polish, safety rails, and often **richer senses** than plain text search.

This [fork](https://github.com/sshaaf/nanocode) keeps that loop and the same six core tools. It adds an optional extra sense for Java workspaces: a **language server**, so the model can ask project-aware questions instead of inferring everything from raw files.

![nanocode Java with LSP](/images/2026/04/nanocode-java-lsp.jpg)

## Does LSP fits the same architecture?

`grep` and `read` are universal and powerful. They are also **syntax-blind**. A symbol might be a field, a local, an import alias, or a string that happens to match. For Java — especially with Maven or Gradle classpaths — the **compiler’s view** of the project is not the same as “all lines containing this word.”

The [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) is the boring industry answer: one process holds the classpath, incremental errors, types, and navigation graph; the client sends small questions (`go to definition`, `hover`, `publishDiagnostics`) and gets structured answers.

nanocode is a thin client in that sense: it forwards requests and prints results. Wiring **Eclipse JDT Language Server** (the same engine behind most Java editor extensions) is not a different *kind* of product — it is **narrower, deeper vision** for one language, and stays optional so a “single-file story” remains when you do not need Java semantics.

## What this fork adds (in practice)

1. **Detection** — If the workspace contains `.java` files, nanocode can offer to turn Java support on.
2. **Local install** — On consent (or via an environment flag), it downloads JDT LS once into your user cache (`~/.cache/nanocode` or `$XDG_CACHE_HOME/nanocode`), not into the repo.
3. **Process + protocol** — A small [LSP4J](https://github.com/eclipse-lsp4j/lsp4j) client drives the server; documents are synced before semantic queries so answers match what is on disk.
4. **Three extra tools** the model sees only when LSP is enabled:
   - **`java_definition`** — Where is this name bound? (1-based line/column, like many editors.)
   - **`java_hover`** — Tooltip-grade material: Javadoc, type hints, etc.
   - **`java_diagnostics`** — Compiler and analysis diagnostics for one file, or a roll-up across files the server has published.

The main script grew; supporting code lives alongside it so newcomers can still read the core agent in one place.

```java
  /**
   * Dispatch tool calls to their respective implementations.
   *
   * Routes tool execution based on the tool name. Basic tools (read, write, edit, glob, grep, bash)
   * are always available. Java LSP tools (java_definition, java_hover, java_diagnostics) require
   * the javaLsp flag to be enabled.
   *
   * @param name The name of the tool to execute
   * @param args JSON arguments for the tool
   * @param javaLsp Whether Java LSP tools are enabled
   * @return Tool execution result, or error message prefixed with ERROR_PREFIX
   */
  static String runTool(String name, JsonNode args, boolean javaLsp) {
      try {
          return switch (name) {
              // Basic file and search tools
              case "read" -> toolRead(args);
              case "write" -> toolWrite(args);
              case "edit" -> toolEdit(args);
              case "glob" -> toolGlob(args);
              case "grep" -> toolGrep(args);
              case "bash" -> toolBash(args);

              // Java LSP tools - require javaLsp flag
              case "java_definition" -> {
                  if (!javaLsp)
                      yield ERROR_PREFIX + "Java LSP not enabled";
                  yield toolJavaDefinition(args);
              }
              case "java_hover" -> {
                  if (!javaLsp)
                      yield ERROR_PREFIX + "Java LSP not enabled";
                  yield toolJavaHover(args);
              }
              case "java_diagnostics" -> {
                  if (!javaLsp)
                      yield ERROR_PREFIX + "Java LSP not enabled";
                  yield toolJavaDiagnostics(args);
              }

              default -> ERROR_PREFIX + "unknown tool " + name;
          };
      } catch (Exception e) {
          // Catch all exceptions and return as error message
          return ERROR_PREFIX + e.getMessage();
      }
  }

  /**
   * Java LSP tool: Go to the definition of a symbol at the specified location.
   *
   * @param args JSON with path (required), line (default 1), column (default 1)
   * @return Location information for the symbol's definition
   */
  static String toolJavaDefinition(JsonNode args) throws Exception {
      return JavaLspSupport.definition(args.get("path").asText(), args.path("line").asInt(1),
              args.path("column").asInt(1));
  }

  /**
   * Java LSP tool: Get type information, signature, and documentation for a symbol at cursor.
   *
   * @param args JSON with path (required), line (default 1), column (default 1)
   * @return Type info, Javadoc, and signature details for the symbol
   */
  static String toolJavaHover(JsonNode args) throws Exception {
      return JavaLspSupport.hover(args.get("path").asText(), args.path("line").asInt(1),
              args.path("column").asInt(1));
  }

  /**
   * Java LSP tool: Get compiler errors and warnings for a file or all cached files.
   *
   * @param args JSON with optional path (empty string = all cached diagnostics)
   * @return List of compiler/LSP diagnostics
   */
  static String toolJavaDiagnostics(JsonNode args) throws Exception {
      return JavaLspSupport.diagnostics(args.path("path").asText(""));
  }

```


## Examples (prompts that now “make sense”)

These are the sorts of tasks where **text tools alone** are brittle, but **JDT + the loop** line up nicely.

**Navigate instead of guessing**

> “In `src/main/java/.../OrderService.java`, around line 48, what type is `discount`? Use java_hover at that position, then java_definition if it is a field.”

The model no longer has to re-derive the type from imports and local inference across half a dozen files unless it wants to double-check.

**Errors with a real classpath**

> “Run java_diagnostics on `PaymentMapper.java` and fix whatever JDT reports; then run `mvn -q test` in bash.”

Diagnostics are tied to how the project is built, not to “did my regex find the word `error` in the log.”

**Onboarding a module**

> “I’m new to this package. Summarize the main entry points: use glob for `*Application.java`, read those files, and for the class that implements `Runnable` or hosts `main`, show java_hover on the superclass or key API types.”

Read + LSP combine the way humans use an IDE: skim files, drill into symbols.

**Guardrails before a large edit**

> “Before we rename this method, list java_diagnostics for the whole workspace (no path) and tell me if anything is already red.”

You still do not get a one-click **rename refactor** in this fork — but you get **honest compiler state**, which is often enough to avoid stepping on a broken build.


```
────────────────────────────────────────────────────────────────────────────────
❯ What does `GET_USERS` mean in `KeycloakOperation`?
────────────────────────────────────────────────────────────────────────────────

⏺ Java_hover(src/main/java/dev/shaaf/keycloak/mcp/server/KeycloakOperation.java)
  ⎿  dev ... +1 lines

⏺ Glob(**/KeycloakOperation.java)
  ⎿  ./src/main/java/dev/shaaf/keycloak/mcp/server/KeycloakOperat...

⏺ Read(src/main/java/dev/shaaf/keycloak/mcp/server/KeycloakOperation.java)
  ⎿     1| package dev.shaaf.keycloak.mcp.server; ... +67 lines

⏺ `GET_USERS` in the `KeycloakOperation` enum is a constant that represents an operation related to retrieving a list of users from the Keycloak server. This operation is part of a group of user operations defined in the enum, which allows users of the `KeycloakTool` to easily reference and execute actions related to user management, such as creating, updating, deleting users, and retrieving user details.
```

To ground this in something non-trivial, the same **Java LSP stack** was exercised against **`keycloak-mcp-server`**: a Quarkus-based MCP server on Java 21, Maven BOM, and many command classes under `dev.shaaf.keycloak.mcp.server`. Typical results: clean diagnostics on command base classes, classpath-backed **hover** on `ObjectMapper` (Jackson JAR version matching the build), and **definition** jumping to the real `KeycloakCommand` source — the sort of answers `grep` alone cannot guarantee.

**Trying JDT without an LLM API key:** the fork ships `LspProbe.java` (JBang), a tiny harness that calls the same `JavaLspSupport` as nanocode’s `java_*` tools. From the nanocode repo:  
`jbang run LspProbe.java /path/to/your-maven-project`  
(optional: `LSP_PROBE_SYNC_SEC` to tune wait for Maven sync.) First run may download JDT (~50 MB) into `~/.cache/nanocode/`; after that you can confirm hover, definition, and diagnostics on disk before wiring up `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, or `OPENAI_API_KEY`.


## Trade-offs worth saying out loud

- **Weight** — JDT LS is not a toy; it is a real JVM product. The agent stays teachable; the server is the same class of dependency serious Java tooling already uses.
- **Tokens** — A richer tool list and longer system text cost a little each request; **targeted** LSP results can replace huge file reads. Net savings are not guaranteed.
- **Trust** — `bash` remains full power. LSP does not sandbox anything; it mainly reduces wrong guesses.
- **Nano** -- Nano but at about 4x more code from the original port.


> Read it, run it, break it, extend it. It’s a great way to understand how tools like Claude Code, Cursor, and Co Pilot work under the hood.  -- [Max](https://xam.dk/blog/nanocode-coding-agent-in-260-lines-of-java/)


## Links

- Nanocode with LSP - https://github.com/sshaaf/nanocode
- A Coding Agent in 260 Lines of Java - https://xam.dk/blog/nanocode-coding-agent-in-260-lines-of-java/
- Original demo agent: github.com/1rgs/nanocode - https://github.com/1rgs/nanocode
- Max’s JBang port: github.com/maxandersen/nanocode - https://github.com/maxandersen/nanocode
- Eclipse JDT Language Server: eclipse-jdtls/eclipse.jdt.ls - https://github.com/eclipse-jdtls/eclipse.jdt.ls

