<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Exchange Item Relation View

The `ExchangeItemRelationView` visualizes the hierarchical structure of exchange items and the relationships between their associated classes in a tree view. You can access `.exchange_item_relation_view` on any `fa.ComponentExchange`. Data collection starts on the allocated exchange items and collects the associated classes through their exchange item elements.

??? example "Exchange Item Relation View of C 28"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("0ab202d7-6497-4b78-9d13-fd7c9a75486c").exchange_item_relation_view
    diag.render("svgdiagram").save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Exchange Item Relation View of C 28.svg">
        <figcaption>[LAB] Exchange Item Relation View of C 28</figcaption>
    </figure>

## Known Issues

One known issue with the current implementation is related to the routing of edges for ExchangeItemElements. The edges might not be routed optimally in certain cases due to the limitations of ELK'S edge routing algorithms.

This issue could potentially be resolved when Libavoid for ELK becomes publicly available. Libavoid is an advanced edge routing library that offers object-avoiding orthogonal and polyline connector routing, which could improve the layout of the edges in the diagram. At that point the exchange item element labels will be added to the diagram as well.

## Check out the code

To understand the collection have a look into the
[`exchange_item_relation_view`][capellambse_context_diagrams.collectors.exchange_item_relation_view]
module.
