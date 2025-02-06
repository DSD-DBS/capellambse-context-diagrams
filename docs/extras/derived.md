<!--
 ~ SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Derived diagram elements

With capellambse-context-diagrams
[`v0.2.36`](https://github.com/DSD-DBS/capellambse-context-diagrams/releases/tag/v0.2.36)
a separate context is built. The elements are derived from the diagram target,
i.e. the system of interest on which `context_diagram` was called on. The
render parameter to enable this feature is called `display_derived_interfaces`
and is available on:

-   `LogicalComponent`s and
-   `SystemComponent`s

!!! example "Context Diagram with derived elements"

    ```py
    from capellambse import MelodyModel

    lost = model.by_uuid("47c3130b-ec39-4365-a77a-5ab6365d1e2e")
    diag = obj.context_diagram
    diag.render(
        "svgdiagram", display_derived_interfaces=True
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of Center-derived.svg" width="1000000">
        <figcaption>Context diagram of <b>Center</b> with derived context</figcaption>
    </figure>

See [`the derivator
functions`][capellambse_context_diagrams.builders.derived.DERIVATORS] to gain
an overview over all supported capellambse types and the logic to derive
elements.
