---
title:       "Introducing rgctl: A Code Knowledge Graph for Engineering Teams and Agents"
subtitle:    "Index once, query many times — structural facts instead of confident guesses"
description: "rgctl turns any repository into a queryable knowledge graph with pre-computed reachability, blast radius, program slicing, taint analysis, and community detection. Built in Rust for speed, designed for LLM agents and humans alike."
date:        2026-09-07
image:       "/images/2026/09/introducing-rgctl.jpg"
tags:        ["rust", "agents", "rgctl", "call-graph", "llm", "tools", "architecture"]
categories:  ["Rust", "AI"]
layout: post
type: post
devto: true
---

# Introducing rgctl: A Code Knowledge Graph for Engineering Teams and Agents

Modern codebases are too large to hold in your head. They are also too large for most LLM context windows. When a coding agent needs to answer "what breaks if I change this function?" on a repository with 50,000 functions, its options are limited: grep through files, read a handful of them, and produce a confident answer that may be structurally wrong.

[rgctl](https://github.com/sshaaf/rgctl) (Reachability Graph Control) takes a different approach. It indexes your repository once into a compact knowledge graph with pre-computed reachability, then serves deterministic, structured answers to questions about architecture, impact, data flow, and more. The graph persists on disk. Queries run in sub-millisecond time. Agents and humans get the same exact results.

This post introduces what rgctl is, how it works, what problems it solves, and how to get started.

### What the R stands for

- **Rust:** Memory-safe, predictable performance at scale without blowing the heap.
- **Reachability:** Pre-computed sparse bitsets keep "what breaks if I change this?" queries sub-second.
- **Rich graph:** 30+ typed relations (CALLS, IMPORTS, CONTAINS), not just files and folders.

## The problem: structural questions deserve structural answers

Consider a typical scenario. You are refactoring a function in a large Java monolith. You need to know:

- Who calls this function, directly and transitively?
- What downstream code depends on it?
- Which community or subsystem does it belong to?
- Is it on a security-sensitive path?
- If I change it, what is the blast radius?

Traditional tools give you text search. IDEs give you find-references for direct callers. Neither gives you the full reachability picture, and neither produces output that a coding agent can consume reliably.

There is a deeper problem: **agents have no memory across sessions.** You spend an afternoon pairing with a coding agent, it builds up context about your codebase — the module boundaries, the hot paths, the coupling between services — and then you close the terminal. When you come back the next morning, that context is gone. The agent starts from zero, burning tokens to re-read files and re-discover structure it already understood yesterday. On a large codebase this warm-up cost is not trivial — it can consume a significant portion of the context window before any real work begins, and the agent may still arrive at a different (or incomplete) mental model each time.

rgctl solves both problems. The graph persists on disk between sessions. It is not reconstructed from file reads — it is pre-computed and deterministic. When the agent starts a new session, it queries the graph and gets the same structural facts it had yesterday, in milliseconds, without burning tokens on re-exploration. The codebase's architecture becomes a durable artifact, not a transient side effect of a conversation.

## How it works: index once, query many times

rgctl follows a two-step model:

![rgctl two-phase pipeline: index once, query many times](/images/2026/09/rgctl-index-query-pipeline.svg)

### Step 1: Discover

The `discover` command walks your repository, parses source files using [tree-sitter](https://tree-sitter.github.io/tree-sitter/) grammars, and builds a typed graph of functions, classes, modules, files, and their relationships. It extracts calls, imports, containment, inheritance, and more — over 30 typed relation types.

```bash
cd your-project
rgctl discover .
```

On a typical project this takes seconds. On large repositories (100k+ functions), it takes a minute or two. The result is a set of artifacts under `{repo}/.rgctl/` — a compact, mmap-backed graph snapshot and pre-computed reachability bitsets.

The reachability bitsets are the key design choice. Instead of computing "what can reach X?" at query time by walking the graph, rgctl pre-computes sparse bitsets during indexing. This is what makes blast-radius queries return in sub-millisecond time even on graphs with hundreds of thousands of nodes.

### Step 2: Query

Once the graph exists, you query it repeatedly without re-indexing:

```bash
# Find all functions matching a pattern
rgctl -f json gql 'MATCH (n:Function) WHERE n.name LIKE "*Service*" RETURN n LIMIT 20'

# Measure change impact
rgctl -f json blast-radius ShoppingCartService

# Find architectural hotspots
rgctl -f json metrics --pagerank

# Natural-language search over functions
rgctl semantic index
rgctl -f json semantic query "checkout flow" --limit 10
```

The `-f json` flag produces stable, versioned JSON output — designed for agent consumption. Without it, rgctl prints human-readable tables and summaries.

## Core capabilities

### Graph Query Language (GQL)

rgctl exposes its graph through a query language that feels familiar if you have used [Cypher](https://neo4j.com/docs/cypher-manual/current/) or [SPARQL](https://www.w3.org/TR/sparql11-query/). You write `MATCH` patterns over typed nodes and edges:

```bash
# Who calls function X?
rgctl -f json gql "MATCH (a:Function)-[:CALLS]->(b:Function) WHERE b.name = 'processOrder' RETURN a"

# What does module Y contain?
rgctl -f json gql "MATCH (m:Module)-[:CONTAINS]->(f:Function) WHERE m.name LIKE '*cart*' RETURN f"

# Transitive call chains up to 3 hops
rgctl -f json gql "MATCH (a:Function)-[:CALLS*1..3]->(b:Function) RETURN a,b LIMIT 50"
```

The graph model includes node types like `Function`, `Class`, `Module`, `File`, and edge types like `CALLS`, `CONTAINS`, `IMPORTS`, `INHERITS`, and `REFERENCES`.

![rgctl knowledge graph model: typed nodes and edges](/images/2026/09/rgctl-graph-model.svg)

### Blast radius

![Blast radius: reverse reachability walk from a changed function](/images/2026/09/rgctl-blast-radius-concept.svg)

This is arguably the most useful command for agent-assisted development. Given a symbol, blast radius walks the call graph backwards along `CALLS` edges and returns every upstream function that could be affected by a change:

```bash
rgctl -f json blast-radius processOrder --depth 3
```

The output includes the affected nodes, their files, communities, and a risk score. Because reachability is pre-computed, this returns instantly regardless of graph size. For a deep dive with a real-world example on Kubernetes, see [Blast Radius for Agent-Assisted Development on Kubernetes](https://shaaf.dev/post/measuring-change-impact-with-blast-radius-on-kubernetes-for-agents/).

Under the hood, rgctl ships two blast-radius implementations. The `BlastRadiusAnalyzer` performs a bounded reverse BFS in O(V+E) — suitable for depth-limited queries. For full transitive closure on large graphs, the `BlastRadiusEngine` first computes [Kosaraju's algorithm](https://en.wikipedia.org/wiki/Kosaraju%27s_algorithm) to condense strongly connected components, then stores reachability as compressed bitsets. This is what makes query time O(1) regardless of graph size — all the work happens once at index time.

You can also attach a policy file for CI enforcement:

```bash
rgctl -f json blast-radius processOrder --policy-file policy.json
```

If the blast radius violates your policy (for example, by touching a protected namespace), the command exits with code 1 — making it suitable for CI gates.

### Community detection

![Community detection: finding architectural subsystems through label propagation](/images/2026/09/rgctl-community-detection.svg)

rgctl runs [label-propagation](https://en.wikipedia.org/wiki/Label_propagation_algorithm) community detection over the call graph, based on [Raghavan et al. (2007)](https://doi.org/10.1103/PhysRevE.76.036106). The algorithm propagates labels across `CALLS` and `USES` edges with deterministic tie-breaking and hub stripping, then scores results with [Newman modularity](https://en.wikipedia.org/wiki/Modularity_(networks)). Communities are clusters of functions that are tightly coupled internally but loosely connected to the rest of the system — they approximate architectural subsystems. The algorithm runs in O(iterations * E), and the iteration count is typically small on real call graphs.

```bash
rgctl -f json gql --macro-name all_communities unused
rgctl -f json gql "MATCH (f:Function) WHERE f.community_id = '12' RETURN f LIMIT 20"
```

This is particularly useful for monolith decomposition. If you are splitting a [Java EE](https://www.oracle.com/java/technologies/java-ee-glance.html) application into microservices, community boundaries give you structural evidence for where to cut, instead of relying on intuition or package names alone. For a worked example, see [Decomposing a Monolith into Microservices with Call Graph Analysis](https://shaaf.dev/post/decomposing-a-monolith-into-microservices-with-call-graph-analysis/).

### Program slicing and taint analysis

With `discover --with-cfg`, rgctl builds control-flow graphs and program dependence graphs for every function. The CFG construction walks the [tree-sitter](https://tree-sitter.github.io/tree-sitter/) AST in O(statements). Dominance frontiers are computed using the [Cooper-Harvey-Kennedy algorithm (SPE 2001)](https://doi.org/10.1002/spe.3780310304) — the same iterative dominator algorithm used in production compilers. From the CFG, rgctl derives the [Program Dependence Graph (PDG)](https://dl.acm.org/doi/10.1145/24039.24041) following [Ferrante et al. (TOPLAS 1987)](https://www.cs.utexas.edu/~pingali/CS395T/2009fa/papers/ferrante87.pdf), encoding both data dependencies (via reaching-definitions dataflow analysis) and control dependencies. This enables two powerful analyses:

**Program slicing** implements [Weiser's backward slicing criterion (ICSE 1981)](https://dl.acm.org/doi/10.1145/800078.802466) — a BFS over the PDG that answers: "Which statements affect the value of variable X at line N?" Both intraprocedural and interprocedural slicing are supported.

```bash
rgctl slice src/Foo.java --line 42 --variable x --function processOrder
```

![Taint analysis: tracing untrusted data from source to sink](/images/2026/09/rgctl-taint-flow.svg)

**Taint analysis** performs forward propagation over the PDG, tracing data from sources (HTTP parameters, user input) to sinks (SQL queries, shell commands), checking whether sanitizers intervene:

```bash
rgctl -f json cpg flows src/Controller.java --line 15 --variable input --function handleRequest
```

These analyses are [CWE](https://cwe.mitre.org/)-aware — the taint engine ships with patterns for SQL injection ([CWE-89](https://cwe.mitre.org/data/definitions/89.html)), cross-site scripting ([CWE-79](https://cwe.mitre.org/data/definitions/79.html)), command injection ([CWE-78](https://cwe.mitre.org/data/definitions/78.html)), and other common vulnerability classes.

### Hybrid Code Property Graph (CPG)

The `cpg` command provides a unified facade over the call graph and CFG/PDG layers:

```bash
# Which fields of a type are mutated, and where?
rgctl -f json cpg mutations --type ShoppingCart --exclude-ctors

# Check CFG/PDG readiness
rgctl -f json cpg status
```

Field mutation tracking is particularly valuable when reviewing DTO safety or validating that a data class is only modified through expected paths.

### Metrics and hotspot detection

Graph centrality metrics identify the most critical nodes in your codebase. rgctl implements three centrality algorithms from the research literature:

- **[PageRank (Page & Brin, 1998)](https://doi.org/10.1109/69.681760)** — `FastPageRank` runs on a `FlatGraphIndex` with adaptive gating for graphs above 500k nodes. Complexity is O(k * E) where k is the iteration count.
- **[Betweenness centrality (Brandes, 2001)](https://doi.org/10.1080/00207160108942084)** — exact Brandes on smaller graphs, sampled Brandes on larger ones to keep runtime tractable.
- **Harmonic centrality** — computed via parallel [HyperLogLog](https://en.wikipedia.org/wiki/HyperLogLog) propagation (HyperBall), which dominates exact harmonic computation on large graphs and feeds into the migration planner's priority scoring.

```bash
# PageRank: which functions are most "important" structurally?
rgctl -f json metrics --pagerank

# Betweenness: which functions are bridges between subsystems?
rgctl -f json metrics --betweenness
```

High-betweenness functions are architectural bottlenecks — they sit on many shortest paths between other nodes, making them coupling hotspots. High-PageRank functions are the ones that cause the most downstream impact when changed. Both are useful inputs for prioritizing refactoring work or migration planning.

### Semantic search

For natural-language queries over the codebase, rgctl offers an opt-in semantic index:

```bash
rgctl semantic index
rgctl -f json semantic query "user authentication flow" --limit 10
```

The default embedder (`vocab`) uses a compiled token vocabulary to produce dense vectors in O(tokens * D), then quantizes them into binary Hamming codes for fast O(n) scan at query time. Before quantization, an optional Jacobi neighbor-blend step (`semantic_diffuse`) propagates embeddings along call-graph edges — so structurally related functions end up closer in the semantic space even if their names differ. A late-fusion re-ranker combines Hamming similarity with graph-based signals from the `AnalysisResults` for the final ranking. For heavier workloads, `--embedder code-daemon` uses ONNX model weights instead of the compiled vocab.

This works at the function level (and optionally at the document-section level for markdown files). It complements GQL — use GQL when you know the exact name, semantic search when you are exploring.

### Migration planning

For large-scale modernization projects, rgctl can generate a package-level migration roadmap:

```bash
rgctl discover . --with-cfg --with-security --with-taint --export-migration-hints
```

This produces a `.rgctl/migration_plan.json` that uses [PageRank](https://en.wikipedia.org/wiki/PageRank), harmonic centrality, and blast radius to prioritize which packages to migrate first, respecting dependency ordering.

For Java-specific migrations, rgctl integrates with [Konveyor](https://konveyor.io/) [Kantra](https://github.com/konveyor/kantra) rules — approximately 2,600 embedded migration rules covering targets like [Quarkus](https://quarkus.io/), [Spring Boot](https://spring.io/projects/spring-boot), and [Jakarta EE](https://jakarta.ee/):

```bash
rgctl discover . --with-kantra --kantra-target quarkus
```

Violations are stored in `.rgctl/kantra_findings.json` and indexed into the graph, so you can query them with GQL:

```bash
rgctl -f json gql "MATCH (r:KantraRule)-[:VIOLATES]->(n) RETURN r, n LIMIT 20"
```

For teams that want a fully orchestrated migration experience, **MigIQ** is an end-to-end migration orchestrator built on top of rgctl. It chains together codebase analysis (via rgctl), requirements gathering, migration planning, and automated execution into a single workflow. You point it at an application, tell it the target stack, and it handles the rest — from indexing the knowledge graph through generating a prioritized migration plan to executing the individual tasks. MigIQ uses rgctl's graph as its structural backbone: communities inform the decomposition strategy, blast radius gates risky changes, and Kantra findings feed directly into the task list.

### CI policy checks

The `check` command enforces policies across the entire codebase:

```bash
rgctl -f json check --policy-file policy.json
```

Exit code 1 means violations were found. The JSON output includes details about what violated and why. This is designed for CI pipelines where you want to prevent architectural regressions — for example, ensuring that a protected module's blast radius does not exceed a threshold.

## Language support

rgctl supports ten Tier 1 languages with full tree-sitter extraction:

- [**Rust**](https://www.rust-lang.org/), [**Python**](https://www.python.org/), [**Java**](https://dev.java/), [**Go**](https://go.dev/), [**TypeScript**](https://www.typescriptlang.org/), [**JavaScript**](https://developer.mozilla.org/en-US/docs/Web/JavaScript), [**C#**](https://learn.microsoft.com/en-us/dotnet/csharp/), [**C**](https://en.cppreference.com/w/c), [**C++**](https://isocpp.org/), [**PHP**](https://www.php.net/)

Additionally, it indexes configuration and infrastructure-as-code files, and parses markdown/MDX for documentation graphs (headings, cross-references, frontmatter).

The [tree-sitter](https://tree-sitter.github.io/tree-sitter/) approach means language support is extensible. Each language gets a parser plugin that maps tree-sitter nodes to the rgctl graph model.

## Designed for agents

![How agents use rgctl: structured facts through the skill layer](/images/2026/09/rgctl-agent-loop.svg)

rgctl was built with LLM coding agents as a first-class consumer. The design reflects this in several ways:

**Compact JSON output.** The `-f json` flag on every command produces versioned, schema-stable JSON. Agents parse structured data instead of scraping CLI tables.

**Deterministic results.** The same query on the same graph always produces the same output. No randomness, no model inference in the loop.

**Low token cost.** Instead of dumping 50 files into context, an agent calls `blast-radius` and gets a structured summary of exactly what is affected. Fewer tokens means faster turns, lower cost, and less hallucination.

**Agent skill.** Running `rgctl install --skill` generates a [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) / [Cursor](https://www.cursor.com/) skill file that teaches the agent how to route natural-language questions to the right rgctl commands. The agent does not need to memorize the CLI — the skill handles translation.

**HTTP mode.** For repeated queries in a session, `rgctl serve` starts an HTTP server with `/api/query` endpoints, avoiding subprocess overhead.

## Architecture and performance

rgctl is written in [Rust](https://www.rust-lang.org/). Discovery uses [Rayon](https://github.com/rayon-rs/rayon) for parallel [tree-sitter](https://tree-sitter.github.io/tree-sitter/) parsing and [Tokio](https://tokio.rs/) for async I/O. The graph snapshot is mmap-backed, meaning queries do not need to deserialize the entire graph into memory.

Typical performance characteristics:

| Operation | Time |
|-----------|------|
| `discover` (small repo, <1k functions) | < 1 second |
| `discover` (large repo, 100k+ functions) | 1-2 minutes |
| `discover --with-cfg` | Adds ~30-60 seconds |
| `blast-radius` query | < 1 millisecond |
| `gql` query | < 1 millisecond |
| `semantic query` | ~10-50 milliseconds |

The pre-computed reachability bitsets are the performance secret. They trade disk space during indexing for instant query-time lookups.

### The analysis module

All graph algorithms live in the [`rgctl-analysis`](https://github.com/sshaaf/rgctl/tree/main/crates/rgctl-analysis) crate. The module table gives a sense of the analytical depth available:

| Module | Algorithm | Complexity |
|--------|-----------|------------|
| `centrality` | PageRank, Brandes betweenness | O(k*E) PageRank; approximate BC |
| `centrality_approx` | Sampled Brandes, parallel HyperBall HLL | Approximate; dominates on large V |
| `community` | Label propagation + modularity | O(iters*E) |
| `blast_radius_scc` | Kosaraju SCC + bitset reachability | O(1) query |
| `blast_radius` | Reverse BFS | O(V+E) |
| `cfg_builder` | CFG from tree-sitter AST | O(stmts) |
| `dominance` | Cooper-Harvey-Kennedy idom | O(n^2) worst |
| `dataflow` | Reaching definitions | O(n*d) |
| `pdg` | Data + control dependencies | O(n*d) |
| `slicing` | Backward BFS slice | O(V+E) |
| `taint` | Forward taint propagation | O(V+E) |
| `semantic_search` | Binary Hamming index + query | O(n) scan |
| `semantic_vocab` | Compiled vocab accumulate | O(tokens*D) |
| `semantic_diffuse` | Jacobi neighbor blend | O(K*E*D) |
| `migration` | Weighted topological sort | O(V+E) |

The `PetGraphView` is built once per analysis pass and shared by reference across analyzers. The `FlatGraphIndex` is a columnar representation used by centrality and blast-radius engines on large graphs where `petgraph`'s adjacency list would be too slow.

## Research foundations

rgctl's design draws on established program analysis and graph algorithm research, as well as recent work on code graphs for LLM agents. The project maintains a detailed [further-reading](https://github.com/sshaaf/rgctl/blob/main/docs/further-reading.md) document mapping each algorithm to its source paper.

Key influences:

- **Classic program analysis** — [Ferrante et al. (TOPLAS 1987)](https://dl.acm.org/doi/10.1145/24039.24041) for the PDG, [Weiser (ICSE 1981)](https://dl.acm.org/doi/10.1145/800078.802466) for program slicing, [Cooper-Harvey-Kennedy (SPE 2001)](https://doi.org/10.1002/spe.3780310304) for fast dominance
- **Graph metrics** — [Page & Brin (1998)](https://doi.org/10.1109/69.681760) for PageRank, [Brandes (2001)](https://doi.org/10.1080/00207160108942084) for betweenness centrality, Boldi & Vigna's HyperBall for approximate harmonic centrality, [Raghavan et al. (2007)](https://doi.org/10.1103/PhysRevE.76.036106) for label-propagation community detection
- **Code graphs for LLM agents** — [CodexGraph (NAACL 2025)](https://arxiv.org/abs/2408.03910) inspired the GQL + JSON API design for agent consumption; [Codebadger (ICSE 2026)](https://arxiv.org/abs/2603.24837) validates the CFG/PDG/slice stack as a CPG for vulnerability analysis; [Reliable Graph-RAG for Codebases (arXiv 2026)](https://arxiv.org/html/2601.08773v1) benchmarks AST-derived knowledge graphs built via tree-sitter — the same extraction approach rgctl uses

The full bibliography, including survey papers and migration-specific research, is available in [docs/further-reading.md](https://github.com/sshaaf/rgctl/blob/main/docs/further-reading.md).

## Getting started

**Install** from [GitHub Releases](https://github.com/sshaaf/rgctl/releases/latest) or build from source:

```bash
git clone https://github.com/sshaaf/rgctl.git
cd rgctl
cargo build --release --bin rgctl
```

**Index your project:**

```bash
cd your-project
rgctl discover .
```

**Run your first queries:**

```bash
# Inventory
rgctl -f json gql 'MATCH (n:Function) RETURN n LIMIT 10'

# Impact analysis
rgctl -f json blast-radius <FunctionName>

# Hotspots
rgctl -f json metrics --pagerank
```

**Install the agent skill:**

The skill is what turns rgctl from a CLI tool into an always-available architectural advisor inside your editor. It is a structured `SKILL.md` file compiled directly into the `rgctl` binary — no external downloads, one command:

```bash
rgctl install --skill
```

This writes skill files into `.claude/skills/rgctl/` and `.cursor/skills/rgctl/`, teaching [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) and [Cursor](https://www.cursor.com/) how to route natural-language questions to the right rgctl commands. Once installed, you can ask your agent things like "what is the blast radius of changing `processOrder`?" or "generate a migration plan for this repo" — the skill handles the translation from natural language to CLI, executes the query, and summarizes the results.

The skill enables workflows that combine structural graph analysis with AI reasoning:

- **Refactoring** — the agent checks blast radius and traces callers before renaming or extracting a function
- **Migration planning** — the agent generates a complete migration roadmap and explains the ordering rationale
- **Cross-language porting** — when rewriting a function from one language to another, the agent extracts data-flow graphs and call neighborhoods from the source to verify the target preserves the same structure
- **Test generation** — the agent analyzes control-flow paths and data dependencies to generate tests that cover actual branch paths
- **Architecture review** — every code review conversation gets access to community structure, coupling metrics, and policy compliance
- **End-to-end migration with MigIQ** — a complete migration orchestrator that uses rgctl for analysis, then automates requirements, planning, and execution in a single workflow

See the full [Agent Skill guide](https://github.com/sshaaf/rgctl/blob/main/docs/guides/agent-skill.md) for worked examples on the CoolStore project.

## When to use rgctl

rgctl is most valuable when:

- You are working on a codebase with **thousands of functions** where grep-based exploration breaks down
- You use **coding agents** ([Cursor](https://www.cursor.com/), [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview), [Aider](https://aider.chat/), [OpenHands](https://github.com/All-Hands-AI/OpenHands)) and want them to make fewer structural mistakes
- You need **impact analysis** before refactoring or during code review
- You are planning a **migration** ([Java EE](https://www.oracle.com/java/technologies/java-ee-glance.html) to [Quarkus](https://quarkus.io/), monolith to microservices) and need dependency-aware ordering — see [Migrating the CoolStore Monolith to Quarkus with rgctl](https://shaaf.dev/post/migrating-coolstore-monolith-to-quarkus-with-rgctl/)
- You want **CI gates** that enforce architectural policies beyond what linting catches
- You need to **decompose a monolith** and want structural evidence for service boundaries

It is less useful for small projects where you can hold the entire codebase in your head, or for questions that require runtime behavior analysis (profiling, dynamic dispatch resolution).

## What comes next

[rgctl](https://github.com/sshaaf/rgctl) is open source under the MIT license. The project is actively developed, with recent releases adding [PHP](https://www.php.net/) Tier 1 support, [Konveyor](https://konveyor.io/) [Kantra](https://github.com/konveyor/kantra) rule integration, and the CLI-first artifact model.

The documentation covers everything from [getting started](https://github.com/sshaaf/rgctl/blob/main/docs/user-guide.md) to [agent recipes](https://github.com/sshaaf/rgctl/blob/main/docs/agent-recipes.md) to [design documents](https://github.com/sshaaf/rgctl/blob/main/docs/design/README.md) for contributors. If you work with large codebases or pair with coding agents, give it a try and see what the graph reveals about your architecture.

## Further reading

- [Blast Radius for Agent-Assisted Development on Kubernetes](https://shaaf.dev/post/measuring-change-impact-with-blast-radius-on-kubernetes-for-agents/) — impact analysis on a 181k-function Go repository
- [Decomposing a Monolith into Microservices with Call Graph Analysis](https://shaaf.dev/post/decomposing-a-monolith-into-microservices-with-call-graph-analysis/) — using community detection and blast radius to find service boundaries
- [Migrating the CoolStore Monolith to Quarkus with rgctl](https://shaaf.dev/post/migrating-coolstore-monolith-to-quarkus-with-rgctl/) — end-to-end Java EE to Quarkus migration walkthrough

Repository: [github.com/sshaaf/rgctl](https://github.com/sshaaf/rgctl)
