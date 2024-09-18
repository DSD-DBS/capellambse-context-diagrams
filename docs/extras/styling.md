<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Applying conditional styling

You can style your rendered diagram-SVGs individually with functions
such that explicit highlighting of objects can be achieved. With this
you can control styling of [`ElkChildType`s][capellambse_context_diagrams.serializers.ElkChildType]
during the serialization while rendering.

Since SVGs can be styled via CSS your options are gigantic. An example
is given by the styling of Actor Functions (i.e. Functions which their
parent Subsystem has the attribute `is_actor=True`) like it is done in
Capella. These appear to be blue.

!!! example "[`styling.BLUE_ACTOR_FNCS`][capellambse_context_diagrams.styling.BLUE_ACTOR_FNCS]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("957c5799-1d4a-4ac0-b5de-33a65bf1519c").context_diagram
    diag.render("svgdiagram").save(pretty=True)
    ```
    produces
    <figure markdown>
        <img src="../../assets/images/Context of educate Wizards.svg" width="1000000">
        <figcaption>Context diagram of Lost SystemFunction with blue actor styling</figcaption>
    </figure>

This is currently the default style which overrides the default from
py-capellambse.

# No symbol rendering

There are some ModelObjects that are displayed as symbols in a diagram (e.g.
Capabilities or Missions). The `.display_symbols_as_boxes` parameter gives you
the control to render these as boxes such that the symbol is displayed as an
icon beside the box-label. Per default it is set to `True`.

??? example "Box-only style for Context diagram of Middle OperationalCapability [OCB]"

    ``` py
    from capellambse import aird

    diag = model.by_uuid("da08ddb6-92ba-4c3b-956a-017424dbfe85").context_diagram
    diag.render("svgdiagram", display_symbols_as_boxes=False).save(pretty=True)
    ```
    produces
    <figure markdown>
        <img src="../../assets/images/Context of Middle symbols.svg" width="1000000">
        <figcaption>Context of Middle OperationalCapability [OCB] no-symbols</figcaption>
    </figure>

??? example "Box-only style for Context diagram of Capability Capability [MCB]"

    ``` py
    from capellambse import aird

    diag = model.by_uuid("9390b7d5-598a-42db-bef8-23677e45ba06").context_diagram
    diag.render("svgdiagram", display_symbols_as_boxes=False).save(pretty=True)
    ```
    produces
    <figure markdown>
        <img src="../../assets/images/Context of Capability symbols.svg" width="1000000">
        <figcaption>Context of Capability Capability [MCB] no-symbols</figcaption>
    </figure>

# No edge labels

The `no_edgelabels` render parameter prevents edge labels from being displayed.

??? example "No-edgelabels style for Context diagram of Capability Capability [MCB]"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("957c5799-1d4a-4ac0-b5de-33a65bf1519c").context_diagram
    diag.render("svgdiagram", no_edgelabels=True).save(pretty=True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of educate Wizards no_edgelabels.svg" width="1000000">
        <figcaption>Context diagram of educate Wizards LogicalFunction no-edgelabels</figcaption>
    </figure>

# Examples for custom styling

You can switch to py-capellambse default styling by overriding the
`render_styles` Attribute with an empty dictionary:

??? example "No styling"

    ``` py
    from capellambse import aird
    from capellambse_context_diagrams import styling

    diag = model.by_uuid("957c5799-1d4a-4ac0-b5de-33a65bf1519c").context_diagram
    diag.render_styles = {}
    diag.render("svgdiagram").save(pretty=True)
    ```
    produces
    <figure markdown>
        <img src="../../assets/images/Context of educate Wizards no_styles.svg" width="1000000">
        <figcaption>Context diagram of educate Wizards LogicalFunction w/o any styles</figcaption>
    </figure>

You probably noticed that the SystemAnalysis diagrams on the index page have
custom styling. There we applied the [SYSTEM_EX_RELABEL][capellambse_context_diagrams.filters.SYSTEM_EX_RELABEL] filter
and [SYSTEM_CAP_STYLING][capellambse_context_diagrams.styling.SYSTEM_CAP_STYLING] style. These styles are applied per default.

Style your diagram elements ([ElkChildType][capellambse_context_diagrams.serializers.ElkChildType]) arbitrarily:

??? example "Red junction point"

    ``` py
    from capellambse import aird
    from capellambse_context_diagrams import styling

    diag = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae").context_diagram
    diag.render_styles = dict(
        styling.BLUE_ACTOR_FNCS,
        junction=lambda obj, serializer: {"stroke": aird.RGB(220, 20, 60)},
    )
    diag.render("svgdiagram").save(pretty=True)
    ```
    produces
    <figure markdown>
        <img src="../../assets/images/Context of Lost red junction.svg" width="1000000">
        <figcaption>Context diagram of Lost SystemFunction with junction point styling</figcaption>
    </figure>

# Display Port Labels

The `display_port_labels` render parameter allows you to display the port labels and `port_label_position` allows you to set the position of the port labels.

??? example display port labels for "Hierarchical diagram"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    obj = model.by_uuid("16b4fcc5-548d-4721-b62a-d3d5b1c1d2eb")
    diagram = obj.context_diagram.render("svgdiagram", display_port_labels=True)
    diagram.save(pretty=True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of Hierarchy display_port_labels.svg" width="1000000">
        <figcaption>Context diagram of Hierarchy LogicalComponenet with type [LAB] display_port_labels</figcaption>
    </figure>
