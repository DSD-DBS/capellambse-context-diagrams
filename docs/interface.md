<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Interfaces (aka ComponentExchanges)

The data is collected by [get_elkdata_for_exchanges][capellambse_context_diagrams.collectors.exchanges.get_elkdata_for_exchanges] which is using the [`InterfaceContextCollector`][capellambse_context_diagrams.collectors.exchanges.InterfaceContextCollector] underneath.

You can render an interface context view just with `context_diagram` on any
[`fa.ComponentExchange`][capellambse.model.crosslayer.fa.ComponentExchange]:

``` py
import capellambse

model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
diag = model.by_uuid("3ef23099-ce9a-4f7d-812f-935f47e7938d").context_diagram
diag.render("svgdiagram").save(pretty=True)
```

<figure markdown>
<img src="../assets/images/Interface Context of Left to right.svg" width="1000000">
<figcaption>Interface context diagram of Left to right LogicalComponentExchange with type [LAB]</figcaption>
</figure>

## Include the interface itself in the context
??? example "Include the interface in the Interface Context"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("fbb7f735-3c1f-48de-9791-179d35ca7b98").context_diagram
    diag.render("svgdiagram", include_interface=True).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Interface Context of Interface.svg" width="1000000">
        <figcaption>Interface context diagram of Interface LogicalComponentExchange with type [LAB]</figcaption>
    </figure>

## Hide functional model elements from the context
??? example "Hide functions and functional exchanges in the Interface Context"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("fbb7f735-3c1f-48de-9791-179d35ca7b98").context_diagram
    diag.render("svgdiagram", hide_functions=True).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Interface Context of Interface-hide-functions.svg" width="1000000">
        <figcaption>Interface context diagram of Interface LogicalComponentExchange with type [LAB]</figcaption>
    </figure>

!!! warning "Interface context only supported for the LogicalComponentExchanges"
