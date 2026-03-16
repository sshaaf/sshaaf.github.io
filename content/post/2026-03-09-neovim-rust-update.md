---
title:       "Adding Rust Support and Some Major updates to My Neovim Config"
date:        2026-03-09
image:       "/images/2026/03/neovim-screenshot.jpg"
tags:        ["neovim", "rust", "java", "tools"]
categories:  ["Java", "Rust"]
layout: post
type: post
---

It's been about 8 months since my [last update on neovim4j](https://shaaf.dev/post/2025-07-17-neovim4java/), and the config has evolved significantly. The name "neovim4j" is now a bit of a misnomer—while it started as a Java-focused setup, it's grown into a polyglot development environment.

## Rust Support 🦀

The biggest addition is comprehensive **Rust support**. I've integrated:

- **rustaceanvim** for advanced LSP features powered by rust-analyzer
- **crates.nvim** for smart Cargo.toml management and dependency completion
- **codelldb** debugger integration
- **neotest** for running Rust tests directly in the editor

The Rust setup mirrors the Java tooling quality—full LSP, debugging, and testing all working seamlessly. Semantic highlighting is disabled in favor of Treesitter for more colorful syntax highlighting.

## Documentation
I have added documentation for this config as well, so its easy to find keys, perhaps take a tutorial incase you are new to neovim.
Full disclousure I am still learning neovim, I am enjoying it a lot, but my workflow over the years still needs some adjustments.

## Theme Picker
Another important enhancement is Theme picker. 

> Note: The Theme picker does not work in the standard OOTB terminal on my Mac. It probably needs more configuration for true color support, but if you would like to look into it, please feel free to raise an issue and happy to accept PRs.

The fun though is that now I have the same theme in my setup as the Borland Turbo many years ago. If you really would like to go that route ;)

Added a Telescope-based theme switcher (`<Space>ct`) with 8 themes: tokyonight, ayu_dark, catppuccin, gruvbox, onedark, nord, nightfox, and kanagawa. Themes are lazy-loaded for fast startup, and your preference persists across sessions.

## Documentation Site

Created a comprehensive [Hugo-based documentation site](https://shaaf.dev/neovim/) with tutorials covering project setup, code completion, debugging, testing, and common workflows for both Java and Rust development.

## Other Improvements

- **Keymap viewer**: Press `<Space>?` to see all keybindings when stuck
- **AI integration updates**: Refined CodeCompanion setup for Ollama and Gemini
- **Tree-sitter fixes**: Improved syntax highlighting loading
- **Plugin refactoring**: Cleaned up LSP, formatting, and linting configurations

The config remains snappy thanks to lazy.nvim's smart plugin loading. If you're doing Java or Rust development with Neovim, feel free to check it out at [github.com/sshaaf/neovim](https://github.com/sshaaf/neovim).

*Previous post: [Neovim for Java Development (July 2025)](https://shaaf.dev/post/2025-07-17-neovim4java/)*
