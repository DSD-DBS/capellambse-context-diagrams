<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
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
<img src="assets/images/Interface Context of Interface.svg" width="1000000">
<figcaption>Interface context diagram of <b>Interface</b></figcaption>
</figure>

## Features

### Functions & Components

The data is collected by either

-   [portless_collector][capellambse_context_diagrams.collectors.portless.collector] for [`ModelObject`s][capellambse.model.ModelObject] from the Operational Architecture Layer
-   [with_port_collector][capellambse_context_diagrams.collectors.default.collector] for all other Architecture Layers that use ports as connectors of exchanges.

It is served conveniently by [get_elkdata][capellambse_context_diagrams.collectors.get_elkdata].

Available via `.context_diagram` on a [`ModelObject`][capellambse.model.ModelObject] with (diagram-class):

-   ??? example "[`oa.Entity`][capellambse.metamodel.oa.Entity] (OAB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("e37510b9-3166-4f80-a919-dfaac9b696c7").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Environment.svg" width="1000000">
              <figcaption>Context diagram of Environment Entity with type [OAB]</figcaption>
          </figure>

-   ??? example "[`oa.OperationalActivity`][capellambse.metamodel.oa.OperationalActivity] (OAIB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("8bcb11e6-443b-4b92-bec2-ff1d87a224e7").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Eat.svg" width="1000000">
              <figcaption>Context diagram of Activity Eat with type [OAIB]</figcaption>
          </figure>

-   ??? example "[`oa.OperationalCapability`][capellambse.metamodel.oa.OperationalCapability] (OCB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("da08ddb6-92ba-4c3b-956a-017424dbfe85").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Middle.svg" width="1000000">
              <figcaption>Context diagram of Middle OperationalCapability with type [OCB]</figcaption>
          </figure>

-   ??? example "[`ctx.Mission`][capellambse.metamodel.sa.Mission] (MCB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("5bf3f1e3-0f5e-4fec-81d5-c113d3a1b3a6").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Top secret.svg" width="1000000">
              <figcaption>Context diagram of Mission Top secret with type [MCB]</figcaption>
          </figure>

-   ??? example "[`ctx.Capability`][capellambse.metamodel.sa.Capability] (MCB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("9390b7d5-598a-42db-bef8-23677e45ba06").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Capability.svg" width="1000000">
              <figcaption>Context diagram of Capability Capability with type [MCB]</figcaption>
          </figure>

-   [`ctx.SystemComponent`][capellambse.metamodel.sa.SystemComponent] (SAB)

-   ??? example "[`ctx.SystemFunction`][capellambse.metamodel.sa.SystemFunction] (SDFB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Lost.svg" width="1000000">
              <figcaption>Context diagram of Lost SystemFunction with type [SDFB]</figcaption>
          </figure>

-   ??? example "[`la.LogicalComponent`][capellambse.metamodel.la.LogicalComponent] (LAB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("f632888e-51bc-4c9f-8e81-73e9404de784").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Left.svg" width="1000000">
              <figcaption>Context diagram of Left LogicalComponent with type [LAB]</figcaption>
          </figure>

-   ??? example "[`la.LogicalFunction`][capellambse.metamodel.la.LogicalFunction] (LDFB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("957c5799-1d4a-4ac0-b5de-33a65bf1519c").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of educate Wizards.svg" width="1000000">
              <figcaption>Context diagram of educate Wizards LogicalFunction with type [LDFB]</figcaption>
          </figure>

-   ??? example "[`pa.PhysicalComponent`][capellambse.metamodel.pa.PhysicalComponent] (PAB)"

          `PhysicalNodeComponent`

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("fdb34c92-7c49-491d-bf11-dd139930786e").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Physical Component.svg" width="1000000">
              <figcaption>Context of Physical Component [PAB]</figcaption>
          </figure>

          `PhysicalBehaviourComponent`

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("313f48f4-fb7e-47a8-b28a-76440932fcb9").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of PC Software.svg" width="1000000">
              <figcaption>Context diagram of PC Software [PAB]</figcaption>
          </figure>

-   ??? example "[`pa.PhysicalFunction`][capellambse.metamodel.pa.PhysicalFunction] (PDFB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("ee745644-07d7-40b9-ad7a-910dc8cbb805").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of Maintain Switch Firmware.svg" width="1000000">
              <figcaption>Context of Maintain Switch Firmware [PDFB]</figcaption>
          </figure>

-   ??? example "[`pa.PhysicalPort`][capellambse.metamodel.cs.PhysicalPort] (PAB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("c403d4f4-9633-42a2-a5d6-9e1df2655146").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/Context of PP 1.svg" width="1000000">
              <figcaption>Context of PP 1 [PAB]</figcaption>
          </figure>

#### Hierarchy in diagrams

Hierarchical diagrams are diagrams where boxes have child boxes and edges
contained. These form subdiagrams which can be layouted via ELK again.
Hierarchy is identified and supported:

??? example "Hierarchical diagram"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb")
    diagram = obj.context_diagram.render("svgdiagram", display_parent_relation=True)
    diagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="assets/images/Context of Hierarchy.svg" width="1000000">
        <figcaption>Context diagram of Hierarchy LogicalComponenet with type [LAB]</figcaption>
    </figure>

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
