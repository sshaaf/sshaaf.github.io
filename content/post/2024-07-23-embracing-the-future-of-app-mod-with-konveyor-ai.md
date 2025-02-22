---
title:       "Embracing the Future of Application Modernization with KAI"
date:        2024-07-23
image:       "/images/2024/07/23/kai-application-migration-with-llm.jpeg"
tags:        ["java", "migration"]
categories:  ["Java" ]
---

[Konveyor’s](https://www.konveyor.io) main strength lies in its comprehensive approach to migration and modernization. At the core of [Konveyor’s](https://www.konveyor.io) functionality is its powerful analysis engine. This engine performs static source code analysis, identifying anti-patterns and issues that might hinder the application’s operation on a target platform. Utilizing community standards like the Language Server Protocol, Konveyor's analysis engine uses rules designed to aid in various migration scenarios. Users can also create custom rules to address specific migration needs, enhancing Konveyor's flexibility and adaptability.

## Enter Konveyor AI - "KAI"

[Konveyor AI](https://github.com/konveyor/kai), the latest advancement under the Konveyor umbrella, leverages generative AI to further streamline application modernization. The primary goal of Konveyor AI (or Kai) is to automate source code changes, thereby improving the economics of migration and modernization efforts.

> Our approach is to use static code analysis to find the areas in source code that need to be transformed. 'kai' will iterate through analysis information and work with LLMs to generate code changes to resolve incidents identified from analysis. This approach does not require fine-tuning of LLMs, we augment a LLMs knowledge via the prompt, similar to approaches with [RAG](https://arxiv.org/abs/2005.11401) by leveraging external data from inside of Konveyor and from Analysis Rules to aid the LLM in constructing better results. For example, [analyzer-lsp Rules](https://github.com/konveyor/analyzer-lsp/blob/main/docs/rules.md) such as these ([Java EE to Quarkus rulesets](https://github.com/konveyor/rulesets/tree/main/default/generated/quarkus)) are leveraged to aid guiding a LLM to update a legacy Java EE application to Quarkus

There is an [awesome blog post](https://www.konveyor.io/blog/kai-deep-dive-2024/) by [John Matthews](https://github.com/jwmatthews) one of the Lead engineers in the project explaining "Kai" in depth.

### BYO Large Language Model
One of the standout features of Kai is its model-agnostic approach. Unlike other solutions, Kai doesn’t bundle any specific large language model (LLM). Instead, it extends Konveyor to interact with various LLMs, providing the flexibility to use the best-suited model for each specific migration context. This approach ensures that organizations can optimize their migration strategies without being locked into a single technology.

## Practical usecase: From Java EE to Quarkus
> The demo in the following video has changed. View this post for [installation instructions](https://shaaf.dev/post/2025-02-22-migrating-javaee-to-quarkus-using-konveyor-ai/)

{{< youtube cXJPHdETwcY >}}

The short demonstration shows how Konveyor AI facilitates migrations from legacy frameworks like Java EE to modern solutions like Quarkus. The process begins with a static code analysis using the Konveyor CLI, which identifies migration issues within the codebase. Once the analysis is complete, Konveyor AI steps in to generate patches for the identified issues, leveraging LLMs to suggest precise code changes.

For instance, outdated Java EE annotations are seamlessly replaced with their modern Jakarta EE counterparts, and JMS-based message-driven beans were converted to JakartaEE annotations, and legacy technology like EJBs turned into REST end points. These changes can be validated by a developer within an integrated development environment (IDE), showcasing how Konveyor AI integrates into existing developer workflows. Konveyor AI does this by using KAI extension.

For a [detailed demo and presentation](https://www.youtube.com/watch?v=0eh-B55zMPI&t=1s) watch this episode of [OpenShift commons](https://commons.openshift.org/) where [Ramón](https://www.linkedin.com/in/rromannissen/) and I go through the details.

`Why should I use Konveyor AI's or how?` the power of "Kai" lies in its ability to automate repetitive migration tasks, leveraging accumulated knowledge from previous migrations. By focusing on code transformation rather than architectural changes, Kai provides a robust tool for modernizing applications efficiently. It empowers developers to make informed decisions, enabling smoother transitions to modern frameworks and cloud-native environments.

To give the latest build a try head out the to instructions [here](https://github.com/konveyor/kai).


Get involved in the [Konveyor community](https://www.konveyor.io) through their mailing lists, [Slack channels](https://www.konveyor.io/slack/), and [regular meetings](https://www.youtube.com/@konveyor361). 


