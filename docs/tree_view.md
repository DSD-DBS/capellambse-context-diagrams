<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Tree View Diagram

With release [`v0.5.35`](https://github.com/DSD-DBS/py-capellambse/releases/tag/v0.5.35) of [py-capellambse](https://github.com/DSD-DBS/py-capellambse) you can access the
`.tree_view` on [`Class`][capellambse.metamodel.information.Class]
objects. A tree view diagram shows a tree made from all properties of the
parent class.

??? example "Tree view of Root"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b7c7f442-377f-492c-90bf-331e66988bda").tree_view
    diag.render("svgdiagram").save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Tree view of Root.svg">
        <figcaption>[CDB] Tree View Diagram of Root</figcaption>
    </figure>

Additional rendering parameters enable the control over the layout computed by
ELK. The available options are:

1. edgeRouting - Controls the style of the edges.
    - POLYLINE (default)
    - ORTHOGONAL
    - SPLINE
2. algorithm - Controls the algorithm for the diagram layout.
    - layered (default)
    - mr.tree
    - ... Have a look for [all available ELK algorithms](https://eclipse.dev/elk/reference/algorithms.html).
3. direction - The flow direction for the ELK Layered algortihm.
    - DOWN (default)
    - UP
    - RIGHT
    - LEFT
4. partitioning - Enable partitioning. Each recursion level for collecting the
classes is its own partition.
    - True (default)
    - False
5. edgeLabelSide - Controls edge label placement.
    - SMART_DOWN (default)
    - SMART_UP
    - ALWAYS_UP
    - ALWAYS_DOWN
    - DIRECTION_UP
    - DIRECTION_DOWN

Additionally the following render parameters are offered:

1. depth - The depth of the computed tree. Defaults to `None` such that the
whole tree is computed. `depth=1` means that only first level properties and
generalizations are collected.
2. super - Generalizations from the `super` attribute, can be set to
    - ALL
    - ROOT
3. sub - Generalizations from the `sub` attribute, can be set to
    - ALL
    - ROOT

Here is an example that shows how convenient these parameters can be passed
before rendering:

??? example "Tree View of Root"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b7c7f442-377f-492c-90bf-331e66988bda").tree_view
    diag.render(
        "svgdiagram",
        edgeRouting="ORTHOGONAL",
        direction="Right",
        # partitioning=False,
        # edgeLabelsSide="ALWAYS_DOWN",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Tree view of Root-params.svg">
        <figcaption>[CDB] Tree View Diagram of Root</figcaption>
    </figure>

They are optional and don't need to be set all together.

## Check out the code

To understand the collection have a look into the
[`class_tree`][capellambse_context_diagrams.collectors.tree_view] module.
