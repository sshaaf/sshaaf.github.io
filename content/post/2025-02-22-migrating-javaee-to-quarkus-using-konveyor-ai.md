---
title:       "Migrating JavaEE apps using Generative AI and Konveyor AI"
subtitle:    "Static code analysis + Gen-AI"
date:        2025-02-22
image:       "/images/2025/02/22/kai-migration-javaee-quarkus-spring.jpeg"
tags:        ["java", "llm", "migration", "konveyor", "gen-ai"]
categories:  ["Java" ]
---

[Konveyor AI](https://github.com/konveyor/kai) is a tool used to migrate Java applications to different Java frameworks, such as from JavaEE to [Quarkus](https://quarkus.io/) or [Spring](https://spring.io/) or from Spring 5 to 6, using Generative AI and static code analysis. I wrote a detailed post about this last year for the [Java Advent Calendar](https://www.javaadvent.com/2024/12/java-migrations-argh-and-now-large-language-models.html). 

Most recently, we have all been hard at work, bringing a preview for our community of users. In this post, I will outline how you can install and configure Konveyor AI using [OpenAI](https://openai.com/) and make meaningful generations. However, I have chosen OpenAI for the sake of simplicity in this post. Users can choose many other models, which are documented [here](https://github.com/konveyor/kai/blob/main/docs/llm_selection.md).

One of the major changes in the new release is the use of agents. Kai now uses agents to recalibrate the codebase. For example, once a fixed is received from the LLM, Kai checks its validity and whether it's in line with the static code analysis. It also checks for compilation errors, and finally, it compiles the code using, e.g., Maven, so the project is intact. 


Noticeable changes in the latest release, `0.0.11.` 
Kai's backend, which talks to an LLM, is now integrated into the VSCode extension. 
"Kai-FixAll" is no longer available. It's much easier now to select an incident, a file, or a group of incidents, e.g., a group of all `Java.*` to `Jakarta.*` in the entire project, or choosing all `@MessageDriven` annotations and converting them to Reactive messaging, etc. 
Furthermore, the UI is completely revamped. It's easy to configure Konveyor AI via a walkthrough. `provider-settings.json` 
The most interesting change is agents. Kai now uses Agents to recalibrate the codebase. 

Here is a short video explaining the installation process, configuration, and a basic use case for resolving a fix. 

{{< youtube MHKbNYZyRVk >}}


We are shipping weekly releases at this point, and theres alot of great work at play. Don't forget to provide [feedback](https://github.com/konveyor/editor-extensions/issues), or if you are interested in contributing, join us in the [Kubernetes Slack community](https://www.konveyor.io/slack/) (`#Konveyor`) 



 

