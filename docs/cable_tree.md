<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Cable Tree View Diagram

The `Cable Tree View` diagram visualizes the cable connections between ports.
You can access `.cable_tree` on any
[`pa.PhysicalLink`][capellambse.metamodel.pa.PhysicalFunction] element.

??? example "Cable Tree View of Control Signal"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("5c55b11b-4911-40fb-9c4c-f1363dad846e").cable_tree
    diag.render("svgdiagram").save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Cable Tree View of Control Signal.svg">
        <figcaption>[LAB] Cable Tree View of Control Signal</figcaption>
    </figure>

## Check out the code

To understand the collection have a look into the
[`cable_tree`][capellambse_context_diagrams.collectors.cable_tree]
module.
