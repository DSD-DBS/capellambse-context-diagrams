<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Realization View Diagram

With release
[`v0.5.42`](https://github.com/DSD-DBS/py-capellambse/releases/tag/v0.5.42) of
[py-capellambse](https://github.com/DSD-DBS/py-capellambse) you can access the
`.realization_view` on a Component or Function from any layer. A realization
view diagram reveals the realization map that the layers of your model
implement currently. The diagram elements are collected from the
`.realized_components` or `.realized_functions` attribute for the direction
`ABOVE` and `.realizing_components` or `.realizing_functions` for direction
`BELOW`.

??? example "Realization View Diagram of `LogicalFunction` `advise Harry` with `layer_sizing=WIDTH`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("beaf5ba4-8fa9-4342-911f-0266bb29be45").realization_view
    diag.render(
        "svgdiagram",
        depth=3, # 1-3
        search_direction="ALL", # BELOW; ABOVE and ALL
        show_owners=True,
        layer_sizing="WIDTH", # UNION; WIDTH, HEIGHT and INDIVIDUAL
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of advise Harry WIDTH.svg">
        <figcaption>[CDB] Realization View Diagram of advise Harry</figcaption>
    </figure>

??? example "Realization View Diagram of `PhysicalComponent` `Physical System` with `layer_sizing=WIDTH`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b9f9a83c-fb02-44f7-9123-9d86326de5f1").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="WIDTH",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of Physical System WIDTH.svg">
        <figcaption>[CDB] Realization View Diagram of Physical System</figcaption>
    </figure>

Additional rendering parameters enable showing owning functions or components,
as well as the depth of traversion (i.e. `1`-`3`) and control on sizing of the
layer boxes. They are put to display the maximum amount of diagram elements per
default. The available options:

1. search_direction - The direction to traverse the realiz(ing/ed) elements.
    - ALL (default)
    - ABOVE
    - BELOW
2. show_owners - Collect parent boxes for every realiz(ing/ed) element.
    - True (default)
    - False
3. layer_sizing - Control even layer box sizing.
    - WIDTH (default)
    - HEIGHT
    - UNION - WIDTH + HEIGHT
    - INDIVIDUAL - Every layer box has minimal size to just contain its
      children.

## Examples

??? example "Realization View Diagram of `LogicalFunction` `advise Harry` for `layer_sizing=HEIGHT`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("beaf5ba4-8fa9-4342-911f-0266bb29be45").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="HEIGHT",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of advise Harry HEIGHT.svg">
        <figcaption>[CDB] Realization View Diagram of advise Harry</figcaption>
    </figure>

??? example "Realization View Diagram of `PhysicalComponent` `Physical System` for `layer_sizing=HEIGHT`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b9f9a83c-fb02-44f7-9123-9d86326de5f1").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="HEIGHT",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of Physical System HEIGHT.svg">
        <figcaption>[CDB] Realization View Diagram of Physical System</figcaption>
    </figure>

??? example "Realization View Diagram of `LogicalFunction` `advise Harry` for `layer_sizing=UNION`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("beaf5ba4-8fa9-4342-911f-0266bb29be45").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="UNION",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of advise Harry UNION.svg">
        <figcaption>[CDB] Realization View Diagram of advise Harry</figcaption>
    </figure>

??? example "Realization View Diagram of `PhysicalComponent` `Physical System` for `layer_sizing=UNION`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b9f9a83c-fb02-44f7-9123-9d86326de5f1").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="UNION",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of Physical System UNION.svg">
        <figcaption>[CDB] Realization View Diagram of Physical System</figcaption>
    </figure>

??? example "Realization View Diagram of `LogicalFunction` `advise Harry` for `layer_sizing=INDIVIDUAL`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("beaf5ba4-8fa9-4342-911f-0266bb29be45").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="INDIVIDUAL",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of advise Harry INDIVIDUAL.svg">
        <figcaption>[CDB] Realization View Diagram of advise Harry</figcaption>
    </figure>

??? example "Realization View Diagram of `PhysicalComponent` `Physical System` for `layer_sizing=INDIVIDUAL`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b9f9a83c-fb02-44f7-9123-9d86326de5f1").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
        layer_sizing="INDIVIDUAL",
    ).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of Physical System INDIVIDUAL.svg">
        <figcaption>[CDB] Realization View Diagram of Physical System</figcaption>
    </figure>

??? info "Alignment of diagram elements"

    With elkjs@0.9.2 ELK's rectpacking algorithm is correctly using the content alignment enumeration.

## Check out the code

To understand the collection have a look into the
[`realization_view`][capellambse_context_diagrams.collectors.realization_view]
module.
