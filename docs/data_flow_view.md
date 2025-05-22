<!--
 ~ SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# DataFlow View Diagram

The
`.data_flow_view` attribute is accessable the following class types:

## OperationalCapability
!!! example "DataFlow View Diagram of [`OperationalCapability`][capellambse.metamodel.oa.OperationalCapability]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("3b83b4ba-671a-4de8-9c07-a5c6b1d3c422").data_flow_view
    diag.as_svgdiagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/DataFlow view of Eat food.svg">
        <figcaption>[OAIB] DataFlow View Diagram of Eat food</figcaption>
    </figure>

## Capability
!!! example "DataFlow View Diagram of [`Capability`][capellambse.metamodel.sa.Capability]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("9390b7d5-598a-42db-bef8-23677e45ba06").data_flow_view
    diag.as_svgdiagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/DataFlow view of Capability.svg">
        <figcaption>[SDFB] DataFlow View Diagram of Capability</figcaption>
    </figure>

## CapabilityRealization
!!! example "DataFlow View Diagram of [`CapabilityRealization`][capellambse.metamodel.la.CapabilityRealization]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("72147e11-70df-499b-a339-b81722271f1a").data_flow_view
    diag.as_svgdiagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/DataFlow view of CapabilityRealization Dataflow.svg">
        <figcaption>[SDFB] DataFlow View Diagram of CapabilityRealization Dataflow</figcaption>
    </figure>

The data flow diagram is similar to the generic context
diagram but it collects differently. Here collection is done from the outside
to the inside, meaning it starts on the involved functions and collects the
edges from there if they exist. This results in revealing missing edges and
possible modelling errors. The diagram elements are collected from the
`.involved_activities` or `.involved_functions` attribute.

## Check out the code

To understand the collection have a look into the
[`data_flow_view`][capellambse_context_diagrams.collectors.dataflow_view]
module.
