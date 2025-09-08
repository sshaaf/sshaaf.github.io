---
title: "Complete local setup development guide for Konveyor Analyzer-lsp 🚀"
date: 2025-09-01
image: "/images/2025/09/konveyor-analyzer-lsp.jpg"
tags: ["java", "migratons", ]
categories: ["Java"]
layout: post
type: post
---


> Build, test, and develop Kantra rules locally with full JDT-LS and multi-language provider support. Some content in this post was generated using an LLM.


Modernizing large, complex codebases is a significant challenge. Identifying migration blockers, deprecated APIs, and technology-specific patterns requires deep, accurate code analysis. The Konveyor Analyzer LSP is engineered to solve this problem by providing a flexible and powerful static analysis engine. It uniquely leverages the Language Server Protocol (LSP) to tap into rich, IDE-level code intelligence for multiple languages.

Konveyor analyzer-lsp is a powerful code analysis engine that supports multiple programming languages through Language Server Protocol (LSP) integration. This guide walks you through setting up a complete local development environment with Java (JDT-LS), Go, Python, Node.js, and YAML providers.

## Prerequisites
Before we begin, you'll need a few essential tools. Each plays a specific role in the ecosystem: Go is used to compile the core analyzer itself, while Java and Maven are required for the JDT Language Server, which provides deep analysis capabilities for Java projects. Podman or Docker is used to manage the containerized language providers, ensuring a clean and isolated environment. Finally, Git is needed to clone the project repository.

- **Go 1.23.9+** - For building the analyzer
- **Java 17+** - Required for JDT-LS
- **Maven** - For Java dependency resolution
- **Podman/Docker** - For external provider containers
- **Git** - For cloning the repository

## Setup Process
The setup process involves two main stages. First, we'll clone the source code and build the konveyor-analyzer command-line tool, which is the core engine that orchestrates the analysis. Second, we'll build and run the various language-specific providers as containerized services. This creates a local micro-ecosystem where the central analyzer can communicate with each language server to inspect code.
#### 1. Clone and Build

```bash
git clone https://github.com/konveyor/analyzer-lsp.git
cd analyzer-lsp

# Build the main analyzer binary
make analyzer

# Build all external providers
make build
```

This creates:
- `konveyor-analyzer` - Main analyzer binary (25MB)
- `konveyor-analyzer-dep` - Dependency analyzer (24MB)
- External provider binaries and Docker images

#### 2. Start External Providers

```bash
# Start Podman machine (if not running)
podman machine start

# Build provider images
make build-java-provider
make build-yq-provider
make build-generic-provider

# Start all providers
podman run --name java-provider -d -p 14651:14651 \
  -v $(pwd)/external-providers/java-external-provider/examples:/examples \
  java-provider --port 14651

podman run --name yq -d -p 14652:14652 \
  -v $(pwd)/examples:/examples \
  yq-provider --port 14652

podman run --name golang-provider -d -p 14653:14653 \
  -v $(pwd)/examples:/examples \
  generic-provider --port 14653

podman run --name nodejs -d -p 14654:14654 \
  -v $(pwd)/examples:/examples \
  generic-provider --port 14654 --name nodejs

podman run --name python -d -p 14655:14655 \
  -v $(pwd)/examples:/examples \
  generic-provider --port 14655 --name pylsp
```

### 3. Verify Setup

```bash
# Check running providers
podman ps

# Test basic functionality
./konveyor-analyzer --provider-settings provider_local_dev.json \
  --rules rule-example.yaml --output-file output.yaml --verbose 5
```

## Rule Development
This is where the real power of the analyzer comes to life. Instead of writing complex programmatic checks, you define declarative rules in YAML. These "Kantra rules" are the brains of the operation, telling the analyzer precisely what to look for in the code. This approach makes it easy to create, share, and maintain a library of checks tailored to your organization's specific modernization goals.

### Understanding Kantra Rules

Kantra rules are YAML-based configurations that define code analysis patterns. Each rule consists of:

```yaml
ruleID: my-custom-rule
message: "Found deprecated API usage"
description: "Detects usage of deprecated APIs"
category: mandatory
effort: 3
when:
  java.referenced:
    pattern: "java\\.util\\.Date"
    location: "method"
```

### Rule Structure

```yaml
ruleID: unique-rule-identifier
message: "Human-readable violation message"
description: "Detailed rule description"
category: mandatory|optional|potential
effort: 1-5  # Migration effort estimate
labels: ["tag1", "tag2"]
when:
  # Condition logic using provider capabilities
```

### Provider Capabilities

#### Java Provider (JDT-LS)
```yaml
when:
  java.referenced:
    pattern: "com\\.example\\.OldClass"
    location: "class"  # class, method, field, annotation, etc.
    annotation: "Deprecated"
```

#### Built-in Provider
```yaml
when:
  builtin.file:
    pattern: "*.xml"
  builtin.xml:
    xpath: "//dependency[groupId='javax.servlet']"
```

#### Go Provider
```yaml
when:
  go.referenced:
    pattern: "oldpackage"
    location: "import"
```

### Creating Custom Rules

1. **Create a new rule file:**
```bash
cat > my-rules.yaml << EOF
rulesets:
  - name: "custom-rules"
    description: "My custom analysis rules"
    rules:
      - ruleID: deprecated-api-usage
        message: "Found deprecated API usage"
        description: "Detects usage of deprecated APIs in Java code"
        category: mandatory
        effort: 3
        when:
          java.referenced:
            pattern: "java\\.util\\.Date"
            location: "method"
EOF
```

2. **Test your rules:**
```bash
./konveyor-analyzer --provider-settings provider_local_dev.json \
  --rules my-rules.yaml --output-file results.yaml
```

## Testing and Validation
Writing a rule is only the first step; ensuring it works correctly and doesn't produce false positives is critical. This section covers the essential workflow for testing your rules. You'll learn how to execute the analyzer against sample code, validate the syntax of your rules against the official schema, and use logging and debugging tools to troubleshoot any issues you encounter.

### Running Analysis

```bash
# Basic analysis
./konveyor-analyzer --rules rule-example.yaml --output-file output.yaml

# With specific provider settings
./konveyor-analyzer --provider-settings provider_local_dev.json \
  --rules rule-example.yaml --output-file output.yaml

# Verbose logging for debugging
./konveyor-analyzer --provider-settings provider_local_dev.json \
  --rules rule-example.yaml --output-file output.yaml --verbose 5
```

### Validating Rules

```bash
# Generate OpenAPI spec for schema validation
./konveyor-analyzer --get-openapi-spec openapi-spec.json

# Check rule syntax
./konveyor-analyzer --rules my-rules.yaml --dry-run
```

### Debugging Common Issues

1. **Provider Connection Issues:**
```bash
# Check provider status
podman ps
podman logs java-provider

# Test provider connectivity
curl http://localhost:14651/health
```

2. **Rule Parsing Errors:**
```bash
# Validate YAML syntax
yamllint my-rules.yaml

# Check OpenAPI schema compliance
./konveyor-analyzer --get-openapi-spec schema.json
```

3. **File Path Issues:**
```bash
# Verify example files exist
ls -la examples/java/
ls -la examples/golang/
```

## Advanced Configuration
While the default settings are great for getting started, real-world projects often require more tailored configurations. This section explores the advanced capabilities of the analyzer, from customizing provider settings for complex project layouts to writing sophisticated rules that chain conditions together. Mastering these configurations will allow you to handle even the most unique analysis scenarios.

### Provider Settings

Create custom provider configurations in `provider_local_dev.json`:

```json
[
  {
    "name": "java",
    "address": "localhost:14651",
    "initConfig": [
      {
        "location": "path/to/java/project",
        "analysisMode": "source-only",
        "providerSpecificConfig": {
          "lspServerName": "java",
          "bundles": "/jdtls/java-analyzer-bundle.jar",
          "lspServerPath": "/jdtls/bin/jdtls"
        }
      }
    ]
  }
]
```

### Analysis Modes

- **`source-only`**: Analyze source code only
- **`full`**: Include dependency analysis

### Custom Variables and Chaining

```yaml
when:
  and:
    - java.referenced:
        pattern: "com\\.example\\.Service"
        location: "class"
        as: "service"
    - java.referenced:
        pattern: "com\\.example\\.Repository"
        location: "class"
        from: "service"  # Reference the previous condition
```

## Output Analysis
After an analysis run completes, the analyzer produces a structured YAML file containing its findings. This output is designed to be both human-readable and machine-parsable, making it easy to understand the results at a glance or integrate them into other tools, CI/CD pipelines, or custom reporting dashboards. Here, we'll break down the structure of the output file.

### Understanding Results

The analyzer generates YAML output with:

```yaml
- name: konveyor-analysis
  tags: ["Java", "Backend"]
  violations:
    rule-id:
      description: "Rule description"
      category: mandatory
      incidents:
        - uri: "file:///path/to/file.java"
          message: "Violation message"
          codeSnip: "source code snippet"
          lineNumber: 42
          variables:
            captured: "value"
      effort: 3
```

### Filtering Results

```bash
# Filter by category
./konveyor-analyzer --rules my-rules.yaml \
  --label-selector "category=mandatory"

# Limit incidents
./konveyor-analyzer --rules my-rules.yaml \
  --limit-incidents 100
```

## Development Workflow
Effective use of the analyzer-lsp follows an iterative development cycle. This section outlines a practical, repeatable workflow for creating, testing, and refining your rules. By adopting this structured approach, you can efficiently build a robust ruleset that delivers accurate and actionable insights for your modernization projects.

### 1. Rule Development Cycle

```bash
# 1. Create/edit rules
vim my-rules.yaml

# 2. Test rules
./konveyor-analyzer --rules my-rules.yaml --output-file test.yaml

# 3. Validate results
cat test.yaml

# 4. Iterate and refine
```

### 2. Integration Testing

```bash
# Test with multiple rule sets
./konveyor-analyzer --rules "rule-example.yaml,my-rules.yaml" \
  --output-file combined-results.yaml

# Test with different provider configurations
./konveyor-analyzer --provider-settings custom-providers.json \
  --rules my-rules.yaml
```

### 3. Performance Optimization

```bash
# Limit code snippets for large files
./konveyor-analyzer --limit-code-snips 10 --rules my-rules.yaml

# Use incident selectors for filtering
./konveyor-analyzer --incident-selector "effort<3" --rules my-rules.yaml
```

## Best Practices
Following established best practices will help you write rules that are not only effective but also maintainable and performant. This section provides key recommendations distilled from community experience, covering everything from how to design clear and efficient rules to strategies for testing them against large and complex codebases.

### Rule Design

1. **Use descriptive rule IDs**: `java-deprecated-api-usage` vs `rule1`
2. **Provide clear messages**: Help developers understand the issue
3. **Set appropriate effort levels**: 1-5 scale for migration complexity
4. **Use meaningful categories**: `mandatory`, `optional`, `potential`

### Performance

1. **Limit incidents**: Use `--limit-incidents` for large codebases
2. **Filter by labels**: Use `--label-selector` to focus on specific rules
3. **Optimize patterns**: Use efficient regex patterns
4. **Use chaining**: Leverage `as` and `from` for complex conditions

### Testing

1. **Test incrementally**: Start with simple rules, add complexity
2. **Validate schemas**: Use OpenAPI spec for rule validation
3. **Check provider logs**: Monitor provider containers for issues
4. **Use verbose logging**: Debug with `--verbose 5`

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Provider connection failed | Check `podman ps` and restart containers |
| Rule parsing errors | Validate YAML syntax and OpenAPI schema |
| No violations found | Check file paths and rule patterns |
| Performance issues | Use incident limits and filtering |

### Getting Help

- **Logs**: Use `--verbose 5` for detailed logging
- **Provider logs**: `podman logs <container-name>`
- **Schema validation**: Generate OpenAPI spec for rule validation
- **Community**: Check Konveyor documentation and GitHub issues

## Conclusion

You now have a fully operational analyzer-lsp development environment with:

- **Java code analysis** with JDT-LS
- **Multi-language support** (Go, Python, Node.js, YAML)
- **Rule development and testing** capabilities
- **OpenAPI schema generation** for validation
- **Comprehensive code analysis workflows**

Start building powerful migration and modernization rules for your codebase!

---

*For more information, visit the [Konveyor slack](https://kubernetes.slack.com/archives/CR85S82A2) or check out the [analyzer-lsp repository](https://github.com/konveyor/analyzer-lsp).*
