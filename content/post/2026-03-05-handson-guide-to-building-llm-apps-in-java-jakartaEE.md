---
title:       "Java+LLMs: A hands-on guide to building LLM Apps in Java"
date:        2026-03-05
image:       "/images/2023/09/08/security.jpeg"
tags:        ["java", "llm"]
categories:  ["Java" ]
layout: post
type: post
---
I had the pleasure to present about building [Java](https://dev.java/learn/) applications using LLMs together with [Bazlur](https://x.com/bazlur_rahman) at [GeeCon 2025](https://2025.geecon.org/). The weather was amazing and [Krakow](https://en.wikipedia.org/wiki/Krak%C3%B3w) is a beautiful historical city. 


{{< youtube Zm6uhQNki_Q >}}


# Key Topics Covered

Here are the key topics from the video with direct links to those sections:

* **[LangChain4j Basics](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D251s):** An introduction to the framework, demonstrating how it abstracts communication with various LLMs like OpenAI and Gemini using builder patterns.
* **[Prompt Engineering](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D443s):** The speakers explain the difference between **System Prompts** (defining the AI's behavior/personality) and **User Prompts** (the specific query).
* **[AI Services & Streaming](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D547s):** A look at how to create high-level interfaces for AI interactions, including streaming responses for real-time chat experiences.
* **[Memory Management](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D720s):** How to provide LLMs with context from previous conversations using providers like `MessageWindowChatMemory` and storing history in databases.
* **[Tools (Function Calling)](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D904s):** A deep dive into how LLMs can trigger Java methods to perform specific tasks, such as fetching web content or compiling Java code.
* **[Jakarta EE Project Generator](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D1306s):** A demonstration of using an LLM tool to generate a complete Jakarta EE project structure via a chat interface.
* **[Retrieval-Augmented Generation (RAG)](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D1635s):** Using **PGVector** and embedding models to store and retrieve private data efficiently.
* **[Chunking and Tokenization](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D1784s):** The importance of segmenting data so the AI receives the right context without exceeding token limits.
* **[Model Context Protocol (MCP)](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D2387s):** An introduction to the standard for connecting AI models to external data sources and tools.
* **[Q&A Session](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DZm6uhQNki_Q%26t%3D2948s):** Discussions on prompt injection, guardrails, and testing non-deterministic AI outputs.

Next up we are both busy building a workshop about Langchain4j and its integration with Spring. If you are interested in learning more join us at [JNation.pt](https://jnation.pt). Bring your laptop the session will be 180 minutes and lots to code about ;)



The source code and step-by-step guide is available here on [github](https://github.com/learnj-ai/llm-jakarta). 
And the [speakerdeck](https://speakerdeck.com/sshaaf/java-plus-llms-a-hands-on-guide-with-bazlur-rahman-and-syed-m-shaaf). 

