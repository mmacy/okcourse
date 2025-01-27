# Roadmap

Features that have been or that might be implemented in the `okcourse` library project.

- [ ] Not implemented
- [x] Implemented
___

- [ ] Library
    - [x] Generate course outlines
    - [x] Generate course lectures from outline
    - [x] Generate course cover art (PNG)
    - [x] Generate course audio (MP3) from lectures
    - [x] Remove `FFmpeg` dependency
    - [ ] Remove `nltk` dependency
    - [ ] Report generator progress
    - [ ] Tests for course generation and audio utils
    - [ ] Anthropic-based generator
    - [ ] Support locally hosted TTS model
- [ ] Docs
    - [x] mkdocs-material site on GitHub Pages
    - [x] README
    - [ ] API reference: all public members have Google Python Style docstrings
    - [ ] Guide: Real *Get started* guide (not just the `README`)
    - [ ] How-to: Determine and estimate cost
    - [ ] How-to: Create a custom course type
    - [ ] Concept: Course generation workflow
    - [ ] Reference: Release notes (automated)
- [ ] Example apps and courses
    - [x] CLI - async
    - [x] Streamlit
    - [ ] CLI - sync
    - [ ] Course MP3 examples for streaming
- [ ] Package dist / Infrastructure
    - [x] Publish `okcourse` package on PyPi
    - [ ] Automate build + release pipeline
    - [ ] Automate tests