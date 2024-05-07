<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# DataFlow View Diagram

You can access the
`.data_flow_view` on an OperationalCapability or Capability. The data flow
diagram is similar to the generic context diagram but it collects differently.
Here collection is done from the outside to the inside, meaning it starts on
the involved functions and collects the edges from there if they exist. This
results in revealing missing edges and possible modelling errors.
The diagram elements are collected from the
`.involved_activities` or `.involved_functions` attribute.

??? example "DataFlow View Diagram of `OperationalCapability` `Eat food`"

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

## Check out the code

To understand the collection have a look into the
[`data_flow_view`][capellambse_context_diagrams.collectors.dataflow_view]
module.
