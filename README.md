# collective.webhook

[![Build Status](https://travis-ci.org/collective/collective.webhook.svg?branch=master)](https://travis-ci.org/collective/collective.webhook)
[![Coverage Status](https://coveralls.io/repos/github/collective/collective.webhook/badge.svg)](https://coveralls.io/github/collective/collective.webhook)

A Plone content rule action for executing HTTP GET or POST with interpolated JSON payload on content event.

## Features

- Can be used to trigger webhooks from Plone content rules.
- Outgoing request are pooled through Plone instance local worker thread throttled by one request / second.

## Examples

- Can be used to trigger CI webhook for building GatsbyJS site from Plone after each time content is being modified.

## Documentation

Full documentation for end users can be found in the "docs" folder.

## Installation

With uv:

```shell
uv venv
uv pip install -e '.[test]'
```

## Contribute

- Issue Tracker: https://github.com/collective/collective.webhook/issues
- Source Code: https://github.com/collective/collective.webhook

## License

The project is licensed under the GPLv2.
