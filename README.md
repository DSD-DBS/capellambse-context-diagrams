<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Context Diagram extension for capellambse

This extension of [py-capellambse](https://github.com/DSD-DBS/py-capellambse) enables generation of views (diagrams) that describe an element context (from a user-defined perspective). This allows systems engineers to do less layouting work and at the same time get diagrams with optimal layouts into the model-derived documents.

The contents of an element context (what elements make it to the context) depend on the element of interest and are selected based on a hand-picked set of rules. However in many cases end user can further customize what and how needs to be in the context view.

The generated views are delivered as SVG images and do not persist in the model itself. This approach enables generation of large number of views at scale (in parallel) in the document production pipeline and also saves quite some XML space in the models. When you rely on generated views for documentation the models can stay lite as they only need to have the engineering / design views (that dont need to have a nice layout).

The layout work is done by [elkjs'](https://github.com/kieler/elkjs) Layered algorithm.

## Generate **Context Diagrams** from your model data!

When the extension is installed you get additional method `.context_diagram` available on those model elements that are already covered by context view definitions.

### Simple context

![Context diagram of **Left**](https://raw.githubusercontent.com/DSD-DBS/capellambse-context-diagrams/main/docs/assets/images/Context%20of%20Left.svg "Context diagram of **Left**")

### Interface context

![Interface context diagram of **Interface**](https://raw.githubusercontent.com/DSD-DBS/capellambse-context-diagrams/main/docs/assets/images/Interface%20Context%20of%20Interface.svg "Interface context diagram of **Interface**")

Have a look at our [documentation](https://capellambse-context-diagrams.readthedocs.io/) to get started and see the capabilities of this extension.

---

Special thanks goes to the developers and maintainers of [Eclipse Layout Kernel™](https://www.eclipse.org/elk/).

# Licenses

Copyright and license information added and maintained via the reuse tool from [Reuse Software](https://reuse.software/).

***Copyright 2022 DB InfraGO AG, own contributions licensed under Apache 2.0 (see full text in [LICENSES/Apache-2.0](https://github.com/DSD-DBS/capellambse-context-diagrams/blob/master/LICENSES/Apache-2.0.txt))***

***Copyright (c) 2021 Kiel University and others, ELK/Sprotty contributions ([elkgraph-json.js](https://github.com/DSD-DBS/capellambse-context-diagrams/blob/master/capellambse_context_diagrams/elkgraph-json.js) & [elkgraph-to-sprotty.js](https://github.com/DSD-DBS/capellambse-context-diagrams/blob/master/capellambse_context_diagrams/elkgraph-to-sprotty.js)) licensed under EPL-2.0***

***Dot-files licensed under CC0-1.0 (see full text in [LICENSES/CC0-1.0](https://github.com/DSD-DBS/capellambse-context-diagrams/blob/master/LICENSES/CC0-1.0.txt))***
