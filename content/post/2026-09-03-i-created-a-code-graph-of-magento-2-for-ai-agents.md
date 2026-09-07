---
title:       "I Created a Code Graph of Magento 2 for AI Agents"
subtitle:    "Tree-sitter PHP extraction, deep analysis, and agent recipes on a 25k-file monolith"
description: "How rgctl indexes Magento Open Source into a structural graph for coding agents — custom PHP Tier 1 plugin, shallow vs deep discover, honest limits on DI-heavy frameworks, and copy-paste agent workflows."
date:        2026-09-03
image:       "/images/2023/09/08/security.jpeg"
tags:        ["agents", "php", "magento", "rgctl", "tree-sitter", "call-graph", "migration"]
categories:  ["Rust"]
layout: post
type: post
devto: true
---

# I Created a Code Graph of Magento 2 for AI Agents

> Reachability Graph Control ([rgctl](https://github.com/sshaaf/rgctl)) indexes a repository once into a compact graph — functions, classes, calls, inheritance, communities — then serves deterministic JSON queries. Agents get structural facts without loading 25,000 PHP files into context.

I wanted to know whether [rgctl](https://github.com/sshaaf/rgctl) could give a coding agent the same kind of map I wish I had on day one of a Magento engagement: **where modules live**, **what calls what**, **which neighborhoods cluster together**, and **what breaks if I touch a service class** — without pretending the framework's dependency injection container is fully visible to static analysis.

This post is use-case driven. If you pair with Cursor, Claude Code, or a custom agent on **large PHP monoliths** (Magento, Symfony, Laravel at scale), the workflow below is what I actually run. Under the hood I'll cover the new **PHP Tier 1 plugin** (tree-sitter, not regex), **shallow vs deep extraction**, and where the graph is honest about what it cannot see.

The corpus is upstream [Magento Open Source](https://github.com/magento/magento2) — cloned locally, indexed with rgctl v0.4.10, not a toy fixture.

## Why Magento, why agents

Magento 2 is a stress test for static tooling:

- **~25,000 PHP files** in `app/`, `lib/`, and `setup/` (excluding `vendor/` and `generated/`)
- **PSR-4 namespaces**, traits, interfaces, generated code paths
- **Symfony-style DI** — constructor injection, `di.xml` preferences, `ObjectManager` at the edges
- **Module boundaries** that do not match folder names in your head

A human opens `module.xml`, greps for `preference`, reads `di.xml`, and builds intuition over weeks. An agent has a context window and `grep`. On a tree this size, "find all usages of `OrderRepository`" often means either reading the wrong ten files or stopping at the first plausible hit.

rgctl's bet is the same one that worked on Kubernetes and Java monoliths in earlier posts: **index once, query many times**, return **small JSON facts** the agent can chain across turns.

## Phase 1: Shallow discover — the structural map

Fetch the corpus (optional — rgctl ships a fetch script for profile repos):

```bash
./scripts/fetch-profile-repos.sh
# → example/magento2/
```

Cold discover on maintainer hardware (release build, empty `.rgctl/`):

```bash
export REPO="$(pwd)/example/magento2"
cd "$REPO"
rm -rf .rgctl
rgctl discover app lib setup -l php -e vendor,generated -v
```

Reference numbers from v0.4.10:

| Metric | Value |
|--------|------:|
| Wall time | **~12 s** |
| PHP files | **25,499** |
| Graph nodes | **~266k** |
| Functions | **~100k** |
| Peak RSS | **~2 GB** |

That is the **shallow** pass: symbols, relations, communities, blast-radius indexes — no CFG, no taint. For an agent's first turn ("what does this codebase look like?"), this is usually enough.

Artifacts land in `{repo}/.rgctl/` — especially `graph.snapshot.bin` and dashboard manifests. Agents should treat that directory as read-only cache; add `.rgctl/` to `.gitignore`.

## Under the hood: tree-sitter, not regex

PHP is **Tier 1** in rgctl — the same class as Java, Go, and Rust. That means a custom `LanguagePlugin` in `crates/rgctl-lang-php/`, backed by **tree-sitter-php**, not the generic Tier 2 regex indexer.

Why that matters for Magento:

| Approach | What you get on `namespace`, traits, `match`, attributes |
|----------|----------------------------------------------------------|
| Regex / line parsers | Fragile; misses nested structures |
| Tree-sitter AST | Grammar-accurate nodes; same pipeline as other Tier 1 languages |

The plugin walks the AST and emits **symbols** (classes, interfaces, traits, enums, methods, functions, arrow functions) and **relations**:

| Relation | Example in Magento-style code |
|----------|------------------------------|
| `Calls` | `$this->orderRepository->save($order)` |
| `Extends` / `Implements` | `class OrderRepository implements OrderRepositoryInterface` |
| `Uses` | `use HasDataChanges;` (trait composition) |
| `Import` | `use Magento\Sales\Api\OrderRepositoryInterface;` |
| `Instantiates` | `new OrderFactory()` |

**Import-aware static calls:** `OrderRepositoryInterface::class` and `SomeService::getInstance()` get `to_qualified_hint` from the file's `use` map — so resolution can tie a call site to a namespaced target when the name is unique in the index.

**Modern PHP surface** (relevant to extensions and newer core code):

- Attributes stored in `metadata.attributes`
- Anonymous classes as `$Anonymous{line}`
- Promoted constructor properties on `fields[]` (DI-style `private readonly OrderRepositoryInterface $orderRepository`)
- `metadata.unresolved` on dynamic calls (`$this->$method()`, variable callees) — the graph keeps the edge but flags that the target is not statically known

Optional: `RGCTL_PHP_ONLY=1` switches to the PHP-only tree-sitter grammar (no inline HTML) for pure `.php` trees.

### What shallow extraction does *not* claim

rgctl is not a PHPStan or Psalm competitor. There is no full type checker inside the plugin — only **bound resolution** from declarations, parameters, fields, and imports. That design choice is intentional: stay fast on whole-repo discover, stay honest when types are interfaces wired at runtime.

On Magento, the symptom is a **sparse call graph**: many SCCs, lots of interface-typed receivers, factory and `ObjectManager` indirection. The graph still tells you **that** a method invokes something; it often cannot name the single concrete callee. More on that in [Honest limits](#honest-limits-di-and-sparse-calls).

## Phase 2: Deep discover — CFG, taint, field mutations

When an agent needs **control flow**, **data-flow-ish facts**, or **security patterns**, run deep discover:

```bash
rgctl discover app lib setup -l php -e vendor,generated \
  --with-cfg --with-security --with-taint -v
```

Reference cold numbers (same hardware):

| Metric | Value |
|--------|------:|
| Wall time | **~33 s** |
| CFG functions | **~100k** |
| Field writes indexed | **~58k** |
| Peak RSS | **~5.7 GB** |

Deep pass adds:

| Layer | Agent use |
|-------|-----------|
| **CFG / PDG** | `inspect`, `slice`, `cpg flows` — "what happens between line 40 and the `save()` call?" |
| **Taint** | Discover-time patterns: `$_FILES`, `filter_input`, PDO `prepare` / SQL sinks |
| **Field mutations** | `cpg mutations --type Order` — cart/DTO safety, state change neighborhoods |
| **Security scan** | Config-like files when `--with-security` is on |

On Magento's core, **taint hit count was very low** (two flows in our cold run) — framework wrappers and indirection mean discover-time heuristics miss most real sinks. That is a finding, not a failure: agents should not treat "zero taint" as "safe"; they should treat it as "pattern library did not match this framework."

Warm re-run on the same tree dropped to **~12 s** wall — cache reuse in `.rgctl/` is real for iterative agent sessions.

## Honest limits: DI and sparse calls

Magento's DI is the elephant in the room. Constructor injection through interfaces is correct at runtime and invisible to naive static resolution:

```php
public function __construct(
    private readonly OrderRepositoryInterface $orderRepository,
) {}
```

rgctl records the **parameter type** on the constructor and the **field** on the class. A call like `$this->orderRepository->get($id)` may not resolve to a unique `Calls` edge to `Magento\Sales\Model\OrderRepository::get` — because the declared type is the interface, and the binding lives in `etc/di.xml`.

We track follow-up work in [issue #75](https://github.com/sshaaf/rgctl/issues/75): CHA-lite candidate edges, config parsers for `di.xml`, and `metadata.candidates` on unresolved calls.

**For agents today:** combine structural queries with module artifacts you already trust:

```bash
# Graph: who implements this interface in-repo?
rgctl -f json gql \
  "MATCH (c:Class)-[:IMPLEMENTS]->(i:Interface)
   WHERE i.qualified_name CONTAINS 'OrderRepository'
   RETURN c.qualified_name LIMIT 20"

# Source: preferences in DI config (agent reads file or rgrep)
rgrep 'OrderRepositoryInterface' app/code/**/etc/di.xml
```

The graph narrows the search space; it does not replace reading `di.xml`.

## Agent workflow: copy-paste recipes

Install the agent skill once per machine (writes `AGENTS.md` recipes into Cursor / Claude config):

```bash
rgctl install --skill --force
```

Standard session:

```bash
export REPO=/path/to/magento2
rgctl -r "$REPO" discover app lib setup -l php -e vendor,generated
```

All queries below assume **`-f json`** and parse `schema_version` + payload from stdout — never scrape stderr.

### 1. Inventory before editing

```bash
# How many service classes in a module path?
rgctl -f json gql \
  "MATCH (n:Class) WHERE n.file_path CONTAINS 'Magento/Sales'
   RETURN n.qualified_name LIMIT 50"

# Functions named like plugins (Magento convention)
rgctl -f json gql \
  "MATCH (f:Function) WHERE f.name LIKE '*Plugin*'
   RETURN f.name, f.file_path LIMIT 30"
```

### 2. Blast radius before a refactor

```bash
rgctl -r "$REPO" -f json blast-radius save --class OrderRepository
```

If the symbol is ambiguous, rgctl returns remediation text — agents must retry with `--class` or `path/to/file.php::method`, not pick a random row.

Use `gatekeeping.policy_status` with a policy file when you want a hard stop:

```json
{ "max_impact_nodes": 80 }
```

### 3. Community = module neighborhood

Community detection clusters functions that call each other densely — often aligned with module boundaries:

```bash
rgctl -f json gql --macro-name all_communities unused
rgctl -f json gql \
  "MATCH (f:Function) WHERE f.community_id = '42' RETURN f LIMIT 30"
```

An agent planning "extract this feature to a microservice" can ask for the community around a REST entrypoint instead of listing every file under `Controller/`.

### 4. Deep slice on a suspicious method

After `--with-cfg`:

```bash
rgctl -f json cpg slice --function execute --file app/code/Magento/Sales/Model/OrderRepository.php
rgctl -f json cpg flows app/code/.../OrderRepository.php --line 120 --variable $order --function save
```

### 5. Semantic search (optional second index)

```bash
rgctl semantic index --embedder hash
rgctl -f json semantic query "cancel order workflow" --limit 10
```

Semantic complements the graph; it does not replace `Calls` edges.

### Agent rules that actually help

| Rule | Why |
|------|-----|
| Run `discover` once per branch / after large pulls | Stale graph → wrong blast radius |
| Prefer `gql` / `blast-radius` over reading random `Model/` files | Token budget |
| Treat `metadata.unresolved` calls as "unknown callee" | Do not invent targets |
| On DI-heavy classes, follow `IMPLEMENTS` + `di.xml` | Graph + config, not graph alone |
| Use `-f json` only | Stable machine output |

See [agent-recipes.md](https://shaaf.dev/rgctl/docs/agent-recipes.md) and [AGENTS.md](https://github.com/sshaaf/rgctl/blob/main/AGENTS.md) for the full command matrix.

## When the graph is enough vs when to use the IDE

| Task | Start with |
|------|------------|
| "What module neighborhood is this controller in?" | `gql` + communities |
| "If I change `save()`, what breaks?" | `blast-radius` |
| "Does this file call `curl_exec` anywhere?" | `cpg` / `slice` after `--with-cfg` |
| "What is the runtime DI binding?" | `di.xml`, `setup:di:compile` output, debugger |
| "Will this PHPStan level pass?" | PHPStan — different tool |

## Try it

- **Release:** [rgctl v0.4.10](https://github.com/sshaaf/rgctl/releases/tag/v0.4.10) — PHP Tier 1 in the default binary
- **Small fixture:** `rgctl-tests/ecommerce-php/` — MVC + taint + field-write golden
- **Large fixture:** `./scripts/fetch-profile-repos.sh` → `example/magento2`
- **Docs:** [languages](https://shaaf.dev/rgctl/docs/languages/), [tier-1 PHP parity](https://shaaf.dev/rgctl/docs/tier-1-language-support/)

```bash
rgctl discover . -l php --with-cfg --with-taint
rgctl install --skill --force
```

If you are building agent playbooks for commerce migrations (Magento → something else, or major version jumps), the combination of **fast whole-repo index**, **honest unresolved edges**, and **JSON query recipes** is the piece I wanted documented — not a fake complete call graph that would lie about DI.

Next up on the graph side: [DI-aware call resolution](https://github.com/sshaaf/rgctl/issues/75) — `di.xml` preferences and interface fan-out without inventing unique targets. Until then, agents that know the limits are more trustworthy than agents that guess.
