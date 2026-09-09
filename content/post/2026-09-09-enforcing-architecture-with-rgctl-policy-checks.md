---
title:       "Enforcing Architecture with rgctl Policy Checks"
subtitle:    "Automated guardrails that fail your build before bad coupling ships"
description: "rgctl policy checks let you define architectural constraints as JSON and enforce them in CI. This post walks through the CoolStore WebLogic monolith as a worked example -- policy file format, violation types, blast-radius gates, and a working GitHub Actions workflow."
date:        2026-09-09
image:       "/images/2025/09/learning-rust.jpg"
tags:        ["rust", "rgctl", "ci", "architecture", "policy", "github-actions", "agents"]
categories:  ["Rust", "CI"]
layout: post
type: post
devto: true
---

# Enforcing Architecture with rgctl Policy Checks

[rgctl](https://github.com/sshaaf/rgctl) (Reachability Graph Control) indexes a codebase into a compact knowledge graph -- functions, classes, calls, inheritance, communities -- and serves deterministic, structured answers to questions about architecture, impact, and data flow. You run `rgctl discover .` once, and every subsequent query (`blast-radius`, `metrics`, `gql`) returns sub-millisecond results from the persisted graph. Agents and humans get the same exact facts. No re-reading source files, no confident guesses, no context window gymnastics.

This post is not about querying the graph. It is about using it to **enforce rules** -- automatically, in CI, on every pull request. We will use a real Java EE monolith as the worked example: the [CoolStore WebLogic](https://github.com/sshaaf/coolstore-weblogic) application.

## The example project: CoolStore WebLogic

[CoolStore](https://github.com/sshaaf/coolstore-weblogic) is a Java EE e-commerce monolith originally built for WebLogic. It has a REST layer (`CartEndpoint`, `OrderEndpoint`, `ProductEndpoint`), a service layer (`ShoppingCartService`, `CatalogService`, `PromoService`, `OrderService`, `ShippingService`), JPA model classes, and a JavaScript frontend with bundled vendor libraries (lodash, d3, jQuery DataTables, Angular). It is small enough to follow along, but structurally interesting -- the vendor JavaScript creates deep call graphs that dwarf the Java application code.

![CoolStore WebLogic: application layers -- Java EE monolith with bundled JavaScript vendor libraries](/images/2026/09/coolstore-policy-architecture.svg)

Clone it and index:

```bash
git clone https://github.com/sshaaf/coolstore-weblogic.git
cd coolstore-weblogic
rgctl discover .
```

```
[>] rgctl discover
==> Analyzing: coolstore-weblogic
[✓] Loaded 1227 files from snapshot -> 17417 nodes, 52920 edges (0.0s)
[✓] Analyzed 7526 functions (avg complexity: 1.0, 0 high, 0 medium)
[✓] Detected 13565 communities (modularity: 0.29)
[*] Top hotspot: replace (PageRank: 0.0502)
[!] Found 186 circular dependencies
[✓] Analysis complete
[✓] Saved to .rgctl/ (2.9 MB total)
[✓] Completed in 0.6s
```

17,417 nodes, 52,920 edges, indexed in under a second. The graph is now on disk at `.rgctl/` and ready for policy checks.

## The problem: architecture rules that live in people's heads

Every team has architectural constraints. "The payments module must not depend on legacy." "No single function should affect more than 50 downstream consumers." "High-centrality bridge functions need extra review." These rules exist as tribal knowledge, communicated in onboarding docs and code review comments. They are enforced manually, inconsistently, and after the fact.

Manual enforcement has three failure modes:

1. **Drift.** The rule is forgotten. A new dependency slips in. Nobody notices until it causes a production incident three months later.
2. **Ambiguity.** "Too much coupling" means different things to different reviewers. Without a number, every review is a negotiation.
3. **Scale.** On a codebase with 7,500 functions, no human can evaluate the blast radius of every changed function in a pull request.

rgctl's `check` command solves this by turning architecture rules into a JSON policy file that a CI pipeline can evaluate automatically.

## Policy file format

A policy file is a JSON object with up to four fields:

```json
{
  "max_impact_nodes": 50,
  "centrality_alert_threshold": 0.8,
  "forbidden_crossings": [["legacy", "payments"]],
  "node_domains": {
    "550e8400-e29b-41d4-a716-446655440000": "legacy",
    "6ba7b810-9dad-11d1-80b4-00c04fd430c8": "payments"
  }
}
```

Every field is optional. Omitted fields default to unlimited (no constraint).

| Field | Type | Default | What it checks |
|-------|------|---------|----------------|
| `max_impact_nodes` | integer | unlimited | Fails if any function's blast-radius impact zone exceeds this count |
| `centrality_alert_threshold` | float | unlimited | Fails if any reached node has betweenness centrality above this value |
| `forbidden_crossings` | `[[string, string], ...]` | `[]` | Fails if a blast-radius path crosses between the named domain pair |
| `node_domains` | `{ "uuid": "domain" }` | `{}` | Maps node UUIDs to domain labels used by `forbidden_crossings` |

The simplest possible policy is one field:

```json
{"max_impact_nodes": 25}
```

This says: no function in the codebase may have a blast radius larger than 25 nodes. If any function exceeds that threshold, the check fails.

## Violation types

When a policy rule is broken, rgctl reports a structured violation. There are four types:

### ScaleFailure

Triggered when a function's impact zone exceeds `max_impact_nodes`.

```
scale failure: impact zone size 648 exceeds max 15
```

This is the most common violation. It catches functions that are deeply embedded in the call graph -- utility functions like `indexOf` or `baseIsEqual` that fan out to hundreds of downstream consumers. A change to these functions has outsized blast radius, and the policy forces the team to acknowledge that.

### CascadeHazard

Triggered when a node in the blast-radius impact zone has betweenness centrality above `centrality_alert_threshold`.

```
cascade hazard: node 6ba7b810... betweenness 0.8523 exceeds threshold 0.8000
```

Betweenness centrality measures how often a node sits on the shortest path between other nodes. High-betweenness nodes are bridge functions -- they connect otherwise separate parts of the graph. Changing a function that reaches a bridge node means the blast radius crosses architectural boundaries. The `CascadeHazard` violation flags this.

### DomainIsolation

Triggered when a blast-radius path crosses a `forbidden_crossings` boundary.

```
domain isolation failure: path from 'legacy' to 'payments' via node 550e8400...
```

This requires setting up `node_domains` to assign graph nodes to logical domains, and `forbidden_crossings` to declare which domain pairs must not be connected. The crossing check is bidirectional -- `["legacy", "payments"]` blocks both `legacy -> payments` and `payments -> legacy` paths.

### SanitizationBypass

Triggered by the CPG (Code Property Graph) analysis when a sanitizer on a taint path does not dominate the sink block in the control-flow graph.

```
sanitization bypass: sanitizer 550e8400... does not dominate sink at line 42 (path len 3)
```

This is the most advanced violation type. It requires `discover --with-cfg` to build the control-flow graph and PDG (Program Dependence Graph), and catches cases where a security sanitizer exists on a data-flow path but can be bypassed through an alternate control-flow route.

## Running the first policy check on CoolStore

Create a policy file. We will start with `max_impact_nodes: 15` and `centrality_alert_threshold: 0.8`:

```json
{"max_impact_nodes": 15, "centrality_alert_threshold": 0.8}
```

Save this as `policy.json` in the repository root and run:

```bash
rgctl -f json check --policy-file policy.json
```

**Output (truncated):**

```json
{
  "schema_version": 1,
  "policy": "policy.json",
  "passed": false,
  "violations": [
    {
      "error": "Graph error: scale failure: impact zone size 114 exceeds max 15",
      "symbol": "baseIsEqual"
    },
    {
      "error": "Graph error: scale failure: impact zone size 649 exceeds max 15",
      "symbol": "baseIndexOf"
    },
    {
      "error": "Graph error: scale failure: impact zone size 78 exceeds max 15",
      "symbol": "merge"
    },
    {
      "error": "Graph error: scale failure: impact zone size 818 exceeds max 15",
      "symbol": "isIterateeCall"
    },
    {
      "error": "Graph error: scale failure: impact zone size 900 exceeds max 15",
      "symbol": "isLength"
    },
    {
      "error": "Graph error: scale failure: impact zone size 648 exceeds max 15",
      "symbol": "indexOf"
    },
    {
      "error": "Graph error: scale failure: impact zone size 899 exceeds max 15",
      "symbol": "replace"
    },
    {
      "error": "Graph error: scale failure: impact zone size 18 exceeds max 15",
      "symbol": "getInventory"
    },
    {
      "error": "Graph error: scale failure: impact zone size 16 exceeds max 15",
      "symbol": "_fnInitComplete"
    }
  ]
}
```

The check exits with code **1**. The full output lists over 100 violations, but the pattern is clear: the worst offenders are lodash and jQuery DataTables internals (`isLength` at 900, `replace` at 899, `isIterateeCall` at 818, `indexOf` at 648). The Java application function `getInventory` appears too -- it has a blast radius of 18 nodes because of its callers in `CatalogService` and the downstream `CatalogItemEntity` model.

### Check the exit code

```bash
rgctl check --policy-file policy.json
echo "Exit code: $?"
```

```
Policy violations: 113
Exit code: 1
```

Exit code 1 means the policy failed. Any CI system can use this directly as a gate.

## Per-function blast radius with policy

The `check` command evaluates every function in the graph. When you want to inspect a specific function, use `blast-radius --policy-file` instead.

![Blast radius: pass vs fail -- priceShoppingCart (7 nodes) vs indexOf (648 nodes) at max_impact_nodes: 15](/images/2026/09/coolstore-policy-blast-comparison.svg)

### A function that passes

`priceShoppingCart` is the core pricing method in `ShoppingCartService`. Let's check it:

```bash
rgctl -f json blast-radius priceShoppingCart --policy-file policy.json
```

```json
{
  "gatekeeping": {
    "policy_status": "PASS",
    "violations": []
  },
  "metrics": {
    "direct_callers_count": 5,
    "impact_zone_size": 7,
    "score": 40.35
  },
  "target": {
    "symbol": "priceShoppingCart",
    "canonical_fqn": "ShoppingCartService::priceShoppingCart",
    "file_path": "src/main/java/com/redhat/coolstore/service/ShoppingCartService.java",
    "language": "java",
    "signature": "public void priceShoppingCart(ShoppingCart sc) {"
  },
  "topology": {
    "direct_callers": [
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.add"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.dedupeCartItems"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.set"},
      {"fqn": "com.redhat.coolstore.service.ShoppingCartService.checkOutShoppingCart"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.delete"}
    ],
    "impact_zone": [
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.add"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.dedupeCartItems"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.delete"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.set"},
      {"fqn": "com.redhat.coolstore.service.ShoppingCartService.checkOutShoppingCart"},
      {"fqn": "com.redhat.coolstore.rest.CartEndpoint.checkout"},
      {"fqn": "anonymous"}
    ]
  }
}
```

**`policy_status: "PASS"`**. The impact zone is 7 nodes -- well under the 15-node limit. Five direct callers, all in `CartEndpoint` and `ShoppingCartService` itself. Changing `priceShoppingCart` affects a contained, well-defined set of functions. This is what healthy coupling looks like.

### A function that violates

Now check `indexOf` from the bundled lodash:

```bash
rgctl -f json blast-radius indexOf --policy-file policy.json
```

```json
{
  "gatekeeping": {
    "policy_status": "VIOLATED",
    "violations": [
      {
        "kind": "scale_failure",
        "count": 648,
        "max": 15
      }
    ]
  },
  "metrics": {
    "direct_callers_count": 232,
    "impact_zone_size": 648,
    "score": 72.4
  },
  "target": {
    "symbol": "indexOf",
    "file_path": "src/main/webapp/bower_components/lodash/lodash.js"
  }
}
```

**`policy_status: "VIOLATED"`**. 232 direct callers, 648 nodes in the impact zone. Changing `indexOf` could affect 648 functions across the entire application. The policy rightfully flags this -- nobody should modify a vendored lodash function without understanding that scope.

### Tight policy on Java service code

Let's use a tighter policy (`max_impact_nodes: 8`) and check `getShoppingCart`:

```bash
rgctl -f json blast-radius getShoppingCart \
  --policy-file policy-tight.json
```

```json
{
  "gatekeeping": {
    "policy_status": "VIOLATED",
    "violations": [
      {
        "kind": "scale_failure",
        "count": 10,
        "max": 8
      }
    ]
  },
  "metrics": {
    "direct_callers_count": 6,
    "impact_zone_size": 10,
    "score": 40.5
  },
  "target": {
    "symbol": "getShoppingCart",
    "canonical_fqn": "ShoppingCartService::getShoppingCart"
  }
}
```

With a limit of 8, `getShoppingCart` violates -- its impact zone is 10. Six direct callers (`CartEndpoint.add`, `CartEndpoint.set`, `CartEndpoint.delete`, `CartEndpoint.dedupeCartItems`, `CartEndpoint.getCart`, `ShoppingCartService.checkOutShoppingCart`) plus their downstream consumers push it over. Raise the threshold to 10 and it passes. This is the kind of tuning that policy files are designed for.

## Java application violations at moderate thresholds

With `max_impact_nodes: 10`, the Java application code starts surfacing alongside the vendor JavaScript:

| Symbol | Impact zone | File |
|--------|-------------|------|
| `getShoppingCartItemList` | 12 | `ShoppingCart.java` |
| `getProductByItemId` | 11 | `ProductService.java` |
| `toProduct` | 14 | `Transformers.java` |
| `getCartItemTotal` | 11 | `ShoppingCart.java` |
| `getShippingTotal` | 11 | `ShoppingCart.java` |
| `getInventory` | 18 | `CatalogItemEntity.java` |
| `getCatalogItemById` | 15 | `CatalogService.java` |

These are the Java functions that fan out the most. `getInventory` has the largest blast radius at 18 nodes -- it is used by `CatalogItemEntity` which feeds into `CatalogService`, `ProductService`, and ultimately the REST endpoints. During a migration from WebLogic to, say, Quarkus, these are the functions you would want to refactor first -- they touch the most downstream code.

## Permissive vs strict policies

### Permissive: baseline for a monolith

Start with a high threshold to establish the pipeline and see what you are dealing with:

```json
{"max_impact_nodes": 500, "centrality_alert_threshold": 0.95}
```

```bash
rgctl -f json check --policy-file policy-permissive.json
```

```json
{
  "schema_version": 1,
  "policy": "policy-permissive.json",
  "passed": false,
  "violations": [
    {"symbol": "baseIndexOf", "error": "Graph error: scale failure: impact zone size 649 exceeds max 500"},
    {"symbol": "binaryIndex", "error": "Graph error: scale failure: impact zone size 659 exceeds max 500"},
    {"symbol": "isIterateeCall", "error": "Graph error: scale failure: impact zone size 818 exceeds max 500"},
    {"symbol": "join", "error": "Graph error: scale failure: impact zone size 607 exceeds max 500"},
    {"symbol": "isLength", "error": "Graph error: scale failure: impact zone size 900 exceeds max 500"},
    {"symbol": "slice", "error": "Graph error: scale failure: impact zone size 697 exceeds max 500"},
    {"symbol": "isIndex", "error": "Graph error: scale failure: impact zone size 856 exceeds max 500"},
    {"symbol": "replace", "error": "Graph error: scale failure: impact zone size 899 exceeds max 500"},
    {"symbol": "baseSlice", "error": "Graph error: scale failure: impact zone size 883 exceeds max 500"},
    {"symbol": "indexOf", "error": "Graph error: scale failure: impact zone size 648 exceeds max 500"},
    {"symbol": "indexOfNaN", "error": "Graph error: scale failure: impact zone size 659 exceeds max 500"},
    {"symbol": "binaryIndexBy", "error": "Graph error: scale failure: impact zone size 660 exceeds max 500"},
    {"symbol": "isObjectLike", "error": "Graph error: scale failure: impact zone size 745 exceeds max 500"}
  ]
}
```

Even at 500, 13 functions still violate. All of them are lodash internals. The Java application code passes entirely. This tells you the vendor JavaScript is the structural risk, not the Java services.

### Strict: zero tolerance

```json
{"max_impact_nodes": 0}
```

A `max_impact_nodes` of 0 means any function with any downstream consumer triggers a failure. Useful for smoke-testing the pipeline or for isolated modules where every function is expected to be a leaf.

## Domain isolation

![Domain isolation: forbidden crossings -- policy blocks blast-radius paths between service and rest layers](/images/2026/09/coolstore-policy-domain-isolation.svg)

You are migrating CoolStore from WebLogic. The REST layer and the service layer must not grow new cross-layer dependencies. You want CI to catch any function whose blast radius crosses from `service` into `rest` (or vice versa).

**Step 1:** Find the node UUIDs for functions in each layer:

```bash
rgctl -f json gql \
  "MATCH (n:Function) WHERE n.file_path CONTAINS 'service/' RETURN n"
```

Each node in the response includes an `id` field (UUID). Collect the UUIDs for the service-layer functions and the REST-layer functions.

**Step 2:** Build the policy:

```json
{
  "max_impact_nodes": 50,
  "forbidden_crossings": [["service", "rest"]],
  "node_domains": {
    "60a84e0c-7366-4e65-8c41-98b4411c7d36": "service",
    "26135ad3-6fa3-4fab-bca6-32607ddbff72": "service",
    "b311845f-2bb1-43c5-99b5-90d2e7d6f60b": "service",
    "fd95d5e1-a959-4d7c-92d4-bd20de91dc45": "rest",
    "004895d9-7ebd-46ed-b92f-84ca01ccfed2": "rest",
    "73fb42ed-45dd-46af-86e9-f1306995916c": "rest"
  }
}
```

**Step 3:** Run the check. Any blast-radius path that crosses from a `service` node to a `rest` node (or vice versa) triggers a `DomainIsolation` violation.

The crossing check is bidirectional. Declaring `["service", "rest"]` blocks both directions.

## Git-aware scoping (local development)

The `check` command has a local optimization: it runs `git diff --name-only HEAD` to detect **uncommitted changes in the working tree**. If you have modified files that are not yet committed, `check` evaluates only the functions defined in those files instead of the full graph. This makes the feedback loop fast during local development -- edit a file, run the check, see if your change introduces a policy violation.

If the diff is empty (no uncommitted changes) or git is unavailable, the check falls back to evaluating every function in the graph. This is what happens in CI: a GitHub Actions checkout produces a clean working tree with no uncommitted changes, so `git diff --name-only HEAD` returns nothing and the full graph is evaluated. For CoolStore's 7,500 functions this is still fast (sub-second), but on very large codebases you may want to be aware of this.

## GitHub Actions integration

![GitHub Actions: architecture policy gate -- every pull request is checked against policy.json before merge](/images/2026/09/coolstore-policy-ci-pipeline.svg)

Here is a complete GitHub Actions workflow that runs rgctl policy checks on every pull request:

```yaml
name: Architecture Policy Check

on:
  pull_request:
    branches: [main]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install rgctl
        run: |
          curl -fsSL https://github.com/sshaaf/rgctl/releases/latest/download/rgctl-linux-x86_64.tar.gz \
            | tar xz -C /usr/local/bin

      - name: Discover codebase
        run: rgctl discover .

      - name: Run policy check
        run: rgctl -f json check --policy-file policy.json
```
> Update 09-09-2026: Today, rgctl does not checkout full git history. evaluation is on a clean tree. This means that `check` evaluates every function in the graph, not just the ones modified in the PR. Temporal updates and diffs are planned for a future release.

The workflow does three things:

1. **Checks out the PR branch.** The checkout is a clean tree, so `check` evaluates every function in the graph (the git-aware local optimization does not apply in CI -- see above).
2. **Discovers the codebase** to build the knowledge graph. This step runs once and persists the graph to `.rgctl/`.
3. **Runs the policy check** against `policy.json` at the repository root. If any violation is found, the step fails with exit code 1 and the pull request is blocked.

### Adding violation details to PR comments

For better developer experience, pipe the JSON output into a PR comment:

```yaml
      - name: Run policy check
        id: policy
        continue-on-error: true
        run: |
          rgctl -f json check --policy-file policy.json > policy-result.json
          echo "passed=$(jq -r .passed policy-result.json)" >> "$GITHUB_OUTPUT"

      - name: Comment on PR
        if: steps.policy.outputs.passed == 'false'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(fs.readFileSync('policy-result.json', 'utf8'));
            const violations = result.violations
              .map(v => `- **${v.symbol}**: ${v.error || v.violation}`)
              .join('\n');
            const body = `## Policy Check Failed\n\n${result.violations.length} violation(s) found:\n\n${violations}`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });

      - name: Fail if violations
        if: steps.policy.outputs.passed == 'false'
        run: exit 1
```

This posts a formatted comment listing every violation, so the developer can see exactly which functions broke the policy without digging into the CI logs.

### Caching the graph

For large repositories, the `discover` step can take minutes. Cache the `.rgctl/` directory to skip re-indexing when the source has not changed:

```yaml
      - name: Cache rgctl graph
        uses: actions/cache@v4
        with:
          path: .rgctl
          key: rgctl-${{ hashFiles('**/*.java', '**/*.ts', '**/*.py') }}
          restore-keys: rgctl-

      - name: Discover codebase
        run: rgctl discover .
```

When the cache hits, `discover` detects the existing graph and skips the indexing step.

## Tightening policies over time

![Tightening policies over time -- CoolStore violations at each threshold](/images/2026/09/coolstore-policy-tightening.svg)

A practical adoption path for CoolStore (or any monolith):

1. **Week 1:** Deploy with a permissive policy (`max_impact_nodes: 500`). On CoolStore, this catches 13 lodash internals and lets all Java application code pass. This is your baseline.
2. **Week 2-4:** Lower the threshold (`max_impact_nodes: 50`). The vendor JavaScript dominates the violations. Consider excluding `bower_components/` from indexing if vendor code is not your concern.
3. **Month 2:** Add `centrality_alert_threshold: 0.8`. Start catching bridge functions that connect otherwise separate subsystems.
4. **Month 3+:** Tighten to `max_impact_nodes: 15`. Now Java application functions like `getInventory` (18 nodes) and `getCatalogItemById` (15 nodes) start appearing. These are your refactoring targets.
5. **Ongoing:** Add `forbidden_crossings` for module boundaries you want to enforce. Assign `node_domains` to the key functions in each domain.

Each step produces measurable progress. The violation count in CI is your metric.

## Summary

| What | How |
|------|-----|
| Define rules | Write a `policy.json` with thresholds and domain boundaries |
| Check locally | `rgctl -f json check --policy-file policy.json` |
| Check one function | `rgctl -f json blast-radius priceShoppingCart --policy-file policy.json` |
| CI gate | Add to GitHub Actions; exit code 1 blocks the PR |
| Start permissive | `{"max_impact_nodes": 500}` -- catches only the worst offenders |
| Get strict | `{"max_impact_nodes": 15, "centrality_alert_threshold": 0.8}` |
| Enforce boundaries | Add `forbidden_crossings` and `node_domains` |

Architecture rules should not live in people's heads. They should live in a JSON file, evaluated on every pull request, with a clear pass/fail signal. That is what rgctl policy checks give you.

The CoolStore WebLogic source is at [github.com/sshaaf/coolstore-weblogic](https://github.com/sshaaf/coolstore-weblogic). Clone it, run `rgctl discover .`, write a `policy.json`, and see what breaks.
