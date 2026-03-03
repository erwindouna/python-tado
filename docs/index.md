---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "Tado Async"
  text: "Asynchronous Python client for the Tado API"
  tagline: Control Tado devices from within Python, mainly used for Home Assistant.
  actions:
    - theme: brand
      text: Get Started
      link: /usage
    - theme: alt
      text: API Reference
      link: /api

features:
  - title: Async Support
    details: Fully asynchronous Python client using aiohttp for non-blocking I/O.
  - title: Home Assistant
    details: Designed for use within Home Assistant, but can also be used standalone.
  - title: Comprehensive API
    details: Covers zones, devices, weather, capabilities, overlays, and more.
---

## About

**Tado Async** is a Python library that allows you to control Tado devices.
Although it can be used as a standalone package, its current scope is to be used within Home Assistant.
Not all endpoints and features are fully supported.
This is the continuation project of PyTado.

::: warning
This project is under active development.
:::
