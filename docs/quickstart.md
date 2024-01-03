<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

## Requirements

You need `Python>=3.9` and either `npm`or `node` to be installed. The automatic
layouting is provided by `elkjs` which is installed if it isn't already.

## Installation

With `pip`:
```bash
pip install capellambse_context_diagrams
```

## Enjoy the features

You can now use the `.context_diagram` attribute on the advertised model
elements. Check out the [examples on the home page][functions-components].

??? fail "Troubleshooting"

    If your [`MelodyModel`][capellambse.model.MelodyModel] instance raises an
    error while initializing the entrypoints or your model element
    raises an `AttributeError`, try to reinstall py-capellambse!
