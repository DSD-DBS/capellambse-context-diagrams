<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

## Requirements

You need `Python>=3.9` and [py-capellambse](https://github.com/DSD-DBS/py-capellambse) to be
installed.

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
