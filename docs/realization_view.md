<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Tree View Diagram

With release
[`v0.5.42`](https://github.com/DSD-DBS/py-capellambse/releases/tag/v0.5.42) of
[py-capellambse](https://github.com/DSD-DBS/py-capellambse) you can access the
`.realization_view` on a Component or Function from any layer. A realization
view diagram reveals the realization map that the layers of your model
implement currently. The diagram elements are collected from the
`.realized_components` or `.realized_functions` attribute for the direction
`ABOVE` and `.realizing_components` or `.realizing_functions` for direction
`BELOW`.

??? example "Realization View Diagram of `LogicalFunction` `advise Harry`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("beaf5ba4-8fa9-4342-911f-0266bb29be45").realization_view
    diag.render(
        "svgdiagram",
        depth=3, # 1-3
        search_direction="ALL", # BELOW; ABOVE and ALL
        show_owners=True,
    ).save_drawing(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of advise Harry.svg">
        <figcaption>[CDB] Realization View Diagram of advise Harry</figcaption>
    </figure>

??? example "Realization View Diagram of `PhysicalComponent` `Physical System`"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("b9f9a83c-fb02-44f7-9123-9d86326de5f1").realization_view
    diag.render(
        "svgdiagram",
        depth=3,
        search_direction="ALL",
        show_owners=True,
    ).save_drawing(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Realization view of Physical System.svg">
        <figcaption>[CDB] Realization View Diagram of Physical System</figcaption>
    </figure>

Additional rendering parameters enable showing owning functions or components,
as well as the depth of traversion (i.e. `1`-`3`). They are put to display the
maximum amount of diagram elements per default.

??? bug "Alignment of diagram elements"

    As of [elkjs@0.9.0](https://eclipse.dev/elk/downloads/releasenotes/release-0.9.0.html) ELK's rectpacking algorithm isn't correctly using the
    content alignment enumeration. While developing the Realization View
    [a fix for the horizontal alignment was proposed](https://github.com/eclipse/elk/issues/989).

## Check out the code

To understand the collection have a look into the
[`realization_view`][capellambse_context_diagrams.collectors.realization_view]
module.
