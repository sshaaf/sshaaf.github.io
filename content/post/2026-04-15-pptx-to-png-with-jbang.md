---
title:       "Rendering powerpoint to png files with JBang"
subtitle:    ""
description: ""
date:        2026-04-28
image:       "/images/2026/04/jbang-pptx-2-png.jpg"
tags:        ["java", "llm", "tools"]
categories:  ["Java"]
layout: post
type: post
devto: true
---

Part of my daily work is to create instructions for workshops, and labs. One of the things in that entire content creation process, is to take screenshots and matching instructions and inorder to do that sometimes I need to add arrows, boxes, etc.. Using something like Google docs is pretty easy at that point, drag the screen shot create the overlay items. This time around I ended up having tons of such slides (a little over exaggeration). The next problem, download them as PNG files to add to the instructions. Out of all the nice usability tricks Google docs does not allow me to optimize on this. So I have to download one slide image at a time. yes really!! Well that was some rant, but hey now we have a JBang script that will do the rest. :) 

This post demonstrates how to leverage **JBang** and **Apache POI** to build a zero-ceremony script that renders PPTX slides to high-DPI PNGs.

> JBang: For utility scripts, the overhead of a Maven/Gradle project is a deterrent. [JBang](https://jbang.dev) eliminates this by allowing "script-style" Java execution. It handles dependency resolution, compilation, and caching in the background, making Java a viable alternative to Python or Bash for system automation.

Okay so here is the solution that uses **Apache POI's Common SL (SlideShow)** API to parse the OOXML structure and **Java 2D (Graphics2D)** for the rasterization.

### 1. Dependency Management
Using JBang's `//DEPS` directives, we pull in the necessary POI components. 

```java
///usr/bin/env jbang "$0" "$@" ; exit $?
//DEPS org.apache.poi:poi:5.2.5
//DEPS org.apache.poi:poi-ooxml:5.2.5
//DEPS org.apache.poi:poi-scratchpad:5.2.5
//DEPS org.apache.logging.log4j:log4j-core:2.20.0
```
> **Note:** `poi-ooxml` is required for `.pptx` (XML-based) files, while `poi-scratchpad` provides support for the older `.ppt` (OLE2) format if needed.

### 2. Initializing the SlideShow
We use **Try-with-Resources** to ensure the `FileInputStream` and `XMLSlideShow` containers are disposed of correctly, preventing memory leaks during batch processing.

```java
try (FileInputStream fis = new FileInputStream(pptxFile);
     XMLSlideShow ppt = new XMLSlideShow(fis)) {

    Dimension pgsize = ppt.getPageSize(); // The logical slide dimensions
    List<XSLFSlide> slides = ppt.getSlides();
    // ... iteration logic
}
```

### 3. Scaling and Precision Math
PowerPoint defines slide dimensions in **points** (where 1 point = 1/72 inch). To produce high-resolution output (e.g., 300 DPI), we must calculate a scale factor relative to this 72 DPI baseline.

```java
double scale = targetDpi / 72.0;
int width = (int) Math.ceil(pgsize.width * scale);
int height = (int) Math.ceil(pgsize.height * scale);
```

### 4. Configuring the Graphics Context
To avoid pixelation and "aliased" text, we must explicitly configure the `Graphics2D` rendering pipeline.

| Hint Key | Value | Purpose |
| :--- | :--- | :--- |
| `KEY_ANTIALIASING` | `VALUE_ANTIALIAS_ON` | Smooths vector edges and shapes. |
| `KEY_TEXT_ANTIALIASING` | `VALUE_TEXT_ANTIALIAS_ON` | Ensures readable, sharp typography. |
| `KEY_INTERPOLATION` | `VALUE_INTERPOLATION_BICUBIC` | High-quality image downsampling/upsampling. |
| `KEY_RENDERING` | `VALUE_RENDER_QUALITY` | General preference for fidelity over speed. |

```java
BufferedImage img = new BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB);
Graphics2D graphics = img.createGraphics();

graphics.setRenderingHints(Map.of(
    RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON,
    RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC,
    RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON
));

graphics.scale(scale, scale); // Map logical points to pixel coordinates
```

### 5. Execution and Output
The `slide.draw(graphics)` call is where the heavy lifting happens. Apache POI iterates through the slide's visual tree (shapes, text boxes, images) and issues the corresponding draw commands to our scaled graphics context.

```java
slide.draw(graphics);
ImageIO.write(img, "PNG", new File(outputName));
graphics.dispose();
```

## Running the Script

Once saved as `pptx2png.java`, make the script executable and run it directly. JBang will fetch the JARs on the first run and cache them at `~/.jbang`.

```bash
chmod +x pptx2png.java
./pptx2png.java my_deck.pptx out_prefix 300
```

Well that made life a step easier. ;)