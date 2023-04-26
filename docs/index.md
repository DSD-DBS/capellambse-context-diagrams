<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Context Diagram extension for capellambse

This is a pluggable extension for [py-capellambse](https://github.com/DSD-DBS/py-capellambse)
that extends the [`AbstractDiagram`][capellambse.model.diagram.AbstractDiagram]
base class with [`ContextDiagram`s][capellambse_context_diagrams.context.ContextDiagram] that are layouted by [elkjs'](https://github.com/kieler/elkjs) Layered algorithm.

<figure markdown>
<img src="assets/images/Context of Left.svg" width="1000000">
<figcaption>Context diagram of <b>Left</b></figcaption>
</figure>

Generate **Context Diagrams** from your model data!

<figure markdown>
<img src="assets/images/Interface Context of Left to right.svg" width="1000000">
<figcaption>Interface context diagram of <b>Left to right</b></figcaption>
</figure>

## Features

### Functions & Components

The data is collected by either

- [portless_collector][capellambse_context_diagrams.collectors.portless.collector] for [`ModelObject`s][capellambse.model.common.element.ModelObject] from the Operational Architecture Layer
- [with_port_collector][capellambse_context_diagrams.collectors.default.collector] for all other Architecture Layers that use ports as connectors of exchanges.

It is served conveniently by [get_elkdata][capellambse_context_diagrams.collectors.get_elkdata].

Available via `.context_diagram` on a [`ModelObject`][capellambse.model.common.element.ModelObject] with (diagram-class):

- ??? example "[`oa.Entity`][capellambse.model.layers.oa.Entity] (OAB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("e37510b9-3166-4f80-a919-dfaac9b696c7").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Environment.svg" width="1000000">
            <figcaption>Context diagram of Environment Entity with type [OAB]</figcaption>
        </figure>

- ??? example "[`oa.OperationalActivity`][capellambse.model.layers.oa.OperationalActivity] (OAIB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("8bcb11e6-443b-4b92-bec2-ff1d87a224e7").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Eat.svg" width="1000000">
            <figcaption>Context diagram of Activity Eat with type [OAIB]</figcaption>
        </figure>

- ??? example "[`oa.OperationalCapability`][capellambse.model.layers.oa.OperationalCapability] (OCB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("da08ddb6-92ba-4c3b-956a-017424dbfe85").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Middle.svg" width="1000000">
            <figcaption>Context diagram of Middle OperationalCapability with type [OCB]</figcaption>
        </figure>

- ??? example "[`ctx.Mission`][capellambse.model.layers.ctx.Mission] (MCB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Top secret.svg" width="1000000">
            <figcaption>Context diagram of Mission Top secret with type [MCB]</figcaption>
        </figure>

- ??? example "[`ctx.Capability`][capellambse.model.layers.ctx.Capability] (MCB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("9390b7d5-598a-42db-bef8-23677e45ba06").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Capability.svg" width="1000000">
            <figcaption>Context diagram of Capability Capability with type [MCB]</figcaption>
        </figure>

- [`ctx.SystemComponent`][capellambse.model.layers.ctx.SystemComponent] (SAB)

- ??? example "[`ctx.SystemFunction`][capellambse.model.layers.ctx.SystemFunction] (SDFB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Lost.svg" width="1000000">
            <figcaption>Context diagram of Lost SystemFunction with type [SDFB]</figcaption>
        </figure>

- ??? example "[`la.LogicalComponent`][capellambse.model.layers.la.LogicalComponent] (LAB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("f632888e-51bc-4c9f-8e81-73e9404de784").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of Left.svg" width="1000000">
            <figcaption>Context diagram of Left LogicalComponent with type [LAB]</figcaption>
        </figure>

- ??? example "[`la.LogicalFunction`][capellambse.model.layers.la.LogicalFunction] (LDFB)"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("957c5799-1d4a-4ac0-b5de-33a65bf1519c").context_diagram
        diag.render("svgdiagram").save_drawing(True)
        ```
        <figure markdown>
            <img src="assets/images/Context of educate Wizards.svg" width="1000000">
            <figcaption>Context diagram of educate Wizards LogicalFunction with type [LDFB]</figcaption>
        </figure>

* [`pa.PhysicalComponent`][capellambse.model.layers.pa.PhysicalComponent] (PAB)
* [`pa.PhysicalFunction`][capellambse.model.layers.pa.PhysicalFunction] (PDFB)
* [`pa.PhysicalComponent`][capellambse.model.layers.pa.PhysicalComponent] (PAB)
* [`pa.PhysicalFunction`][capellambse.model.layers.pa.PhysicalFunction] (PDFB)

#### Hierarchy in diagrams

Hierarchical diagrams are diagrams where boxes have child boxes and edges
contained. These form subdiagrams which can be layouted via ELK again.
Hierarchy is identified and supported:

??? example "Hierarchical diagram"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb")
    diagram = obj.context_diagram.render("svgdiagram", include_inner_objects=True)
    diagram.save_drawing(True)
    ```
    <figure markdown>
        <img src="assets/images/Context of Hierarchy.svg" width="1000000">
        <figcaption>Context diagram of Hierarchy LogicalComponenet with type [LAB]</figcaption>
    </figure>

### Interfaces (aka ComponentExchanges)

The data is collected by [get_elkdata_for_exchanges][capellambse_context_diagrams.collectors.exchanges.get_elkdata_for_exchanges] which is using the [`InterfaceContextCollector`][capellambse_context_diagrams.collectors.exchanges.InterfaceContextCollector] underneath.

??? example "[`fa.ComponentExchange`][capellambse.model.crosslayer.fa.ComponentExchange]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("3ef23099-ce9a-4f7d-812f-935f47e7938d").context_diagram
    diag.render("svgdiagram").save_drawing(True)
    ```
    <figure markdown>
        <img src="assets/images/Interface Context of Left to right.svg" width="1000000">
        <figcaption>Interface context diagram of Left to right LogicalComponentExchange with type [LAB]</figcaption>
    </figure>

!!! warning "Interface context only supported for the LogicalComponentExchanges"

### Customized edge routing

!!! note "Custom routing"
    The routing differs from [ELK's Layered Algorithm](https://www.eclipse.org/elk/reference/algorithms/org-eclipse-elk-layered.html): The flow display is disrupted!
    We configure exchanges such that they appear in between the context
    participants. This decision breaks the display of data flow which is one
    of the main aims of ELK's Layered algorithm. However this lets counter
    flow exchanges routes lengths and bendpoints increase.

    <figure markdown>
        <img src="assets/images/Context of Weird guy.svg" width="1000000">
        <figcaption>Context diagram of Weird guy SystemFunction</figcaption>
    </figure>

---

See the code [reference][capellambse_context_diagrams] section for understanding the underlying
implementation.
