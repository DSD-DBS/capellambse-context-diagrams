<!--
 ~ SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Context Diagram extension for capellambse

This is a pluggable extension for [py-capellambse](https://github.com/DSD-DBS/py-capellambse)
that extends the [`AbstractDiagram`][capellambse.model.diagram.AbstractDiagram]
base class with [`ContextDiagram`s][capellambse_context_diagrams.context.ContextDiagram] that are layouted by [elkjs'](https://github.com/kieler/elkjs) Layered algorithm.

<figure markdown>
<img src="assets/images/ContextDiagram of Left.svg" width="1000000">
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

Available via `.context_diagram` on a [`ModelObject`][capellambse.model.ModelObject] with (diagram-class):

-   ??? example "[`oa.Entity`][capellambse.metamodel.oa.Entity] (OAB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("e37510b9-3166-4f80-a919-dfaac9b696c7").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of Environment.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Eat.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Middle.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Top secret.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Capability.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Lost.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Left.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of educate Wizards.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Physical Component.svg" width="1000000">
              <figcaption>ContextDiagram of Physical Component [PAB]</figcaption>
          </figure>

          `PhysicalBehaviourComponent`

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("313f48f4-fb7e-47a8-b28a-76440932fcb9").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of PC Software.svg" width="1000000">
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
              <img src="assets/images/ContextDiagram of Maintain Switch Firmware.svg" width="1000000">
              <figcaption>ContextDiagram of Maintain Switch Firmware [PDFB]</figcaption>
          </figure>

-   ??? example "[`pa.PhysicalPort`][capellambse.metamodel.cs.PhysicalPort] (PAB)"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("c403d4f4-9633-42a2-a5d6-9e1df2655146").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/PhysicalPortContextDiagram of PP 1.svg" width="1000000">
              <figcaption>PhysicalPortContextDiagram of PP 1 [PAB]</figcaption>
          </figure>

### FunctionalChains

The `context_diagram` attribute is also available to `FunctionalChain`s and
`OperationalProcess`es:

??? example "[`fa.FunctionalChain`][capellambse.metamodel.fa.FunctionalChain]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("ec1ecf8b-d58b-4468-9742-6fdfd6cff702").context_diagram
    diag.render("svgdiagram").save(pretty=True)
    ```
    <figure markdown>
        <img src="assets/images/FunctionalChainContextDiagram of Context.svg" width="1000000">
        <figcaption>FunctionalChainContextDiagram of Context [LAB]</figcaption>
    </figure>

and with the following rendering parameters:

- ??? example "`display_parent_relation=False`"

        ``` py
        import capellambse

        model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
        diag = model.by_uuid("ec1ecf8b-d58b-4468-9742-6fdfd6cff702").context_diagram
        diag.render("svgdiagram", display_parent_relation=False).save(pretty=True)
        ```
        <figure markdown>
            <img src="assets/images/FunctionalChainContextDiagram of Context-without-component-allocation.svg" width="1000000">
            <figcaption>FunctionalChainContextDiagram of Context without Component Allocation [LAB]</figcaption>
        </figure>

### OperationalProcess

??? example "[`oa.OperationalProcess`][capellambse.metamodel.oa.OperationalProcess]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("bec38a21-cc4b-4c06-8acf-067bd5f44824").context_diagram
    diag.render("svgdiagram").save(pretty=True)
    ```
    <figure markdown>
        <img src="assets/images/FunctionalChainContextDiagram of OAContext.svg" width="1000000">
        <figcaption>FunctionalChainContextDiagram of OAContext [LAB]</figcaption>
    </figure>

### Hierarchy in diagrams

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
        <img src="assets/images/ContextDiagram of Hierarchy.svg" width="1000000">
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
    <img src="assets/images/ContextDiagram of Weird guy.svg" width="1000000">
    <figcaption>Context diagram of Weird guy SystemFunction</figcaption>
    </figure>


### View modes

#### Whitebox

There are different view modes for context diagrams. `WHITEBOX` is
enabled per **default**.

!!! example "WHITEBOX view mode"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
    diagram = obj.context_diagram.render("svgdiagram", mode="WHITEBOX")
    diagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="assets/images/ContextDiagram of Box-whitebox.svg" width="1000000">
        <figcaption>Context diagram of Box PhysicalComponent with WHITEBOX mode</figcaption>
    </figure>

Additional render parameters for `WHITEBOX` mode are offered via:

-   ??? example "include_external_context=True"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
          diagram = obj.context_diagram.render(
            "svgdiagram", mode="WHITEBOX", include_external_context=True,
          )
          diagram.save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of Box-whitebox_with_external_context.svg" width="1000000">
              <figcaption>Context diagram of Box PhysicalComponent with WHITEBOX mode and External Context display</figcaption>
          </figure>

#### Blackbox

This render parameter conceals internal details to provide a streamlined
black box representation of the system of interest.

!!! example "BLACKBOX view mode"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
    diagram = obj.context_diagram.render("svgdiagram", mode="BLACKBOX")
    diagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="assets/images/ContextDiagram of Box-blackbox.svg" width="1000000">
        <figcaption>Context diagram of Box PhysicalComponent with BLACKBOX mode</figcaption>
    </figure>

Additional render parameters for hiding internal relations (dashed) or
even cyclic internal relations are offered via:

-   ??? example "display_internal_relations=False"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
          diagram = obj.context_diagram.render(
            "svgdiagram", mode="BLACKBOX", display_internal_relations=False
          )
          diagram.save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of Box-blackbox_without_internal_relations.svg" width="1000000">
              <figcaption>Context diagram of Box PhysicalComponent with BLACKBOX mode</figcaption>
          </figure>

-   ??? example "display_cyclic_relations=True"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
          diagram = obj.context_diagram.render(
              "svgdiagram",
              mode="BLACKBOX",
              display_internal_relations=True, # per default
              display_cyclic_relations=True,
          )
          diagram.save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of Box-blackbox_with_internal_cycles.svg" width="1000000">
              <figcaption>Context diagram of Box PhysicalComponent with BLACKBOX mode and Cycle display</figcaption>
          </figure>

-   ??? example "include_external_context=True"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          obj = model.by_uuid("309296b1-cf37-45d7-b0f3-f7bc00422a59")
          diagram = obj.context_diagram.render(
              "svgdiagram",
              mode="BLACKBOX",
              display_internal_relations=True, # per default
              include_external_context=True,
          )
          diagram.save(pretty=True)
          ```
          <figure markdown>
              <img src="assets/images/ContextDiagram of Box-blackbox_with_external_context.svg" width="1000000">
              <figcaption>Context diagram of Box PhysicalComponent with BLACKBOX mode and External Context display</figcaption>
          </figure>
---

See the code [reference][capellambse_context_diagrams] section for understanding the underlying
implementation.
