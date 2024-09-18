<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Interfaces (aka ComponentExchanges)

The data is collected by [get_elkdata_for_exchanges][capellambse_context_diagrams.collectors.exchanges.get_elkdata_for_exchanges] which is using the [`InterfaceContextCollector`][capellambse_context_diagrams.collectors.exchanges.InterfaceContextCollector] underneath.

You can render an interface context view just with `context_diagram` on any
of the following Model elements:

-   ??? example "[`fa.ComponentExchange`][capellambse.metamodel.fa.ComponentExchange]:"

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("3ef23099-ce9a-4f7d-812f-935f47e7938d").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```

          <figure markdown>
              <img src="../assets/images/Interface Context of Left to right.svg" width="1000000">
              <figcaption>Interface context diagram of `Left to right` Logical ComponentExchange with type [LAB]</figcaption>
          </figure>

-   ??? example "[`cs.PhysicalLink`][capellambse.metamodel.cs.PhysicalLink]:"

          Per default port labels are enabled with port label position set to
          ``OUTSIDE``. See [`PORT_LABEL_POSITION`][capellambse_context_diagrams._elkjs.PORT_LABEL_POSITION] for more information about the available options
          for port label positioning.

          ``` py
          import capellambse

          model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
          diag = model.by_uuid("da949a89-23c0-4487-88e1-f14b33326570").context_diagram
          diag.render("svgdiagram").save(pretty=True)
          ```

          <figure markdown>
              <img src="../assets/images/Interface Context of Cable 1.svg" width="1000000">
              <figcaption>Interface context diagram of `Cable 1` PhysicalLink with type [PAB]</figcaption>
          </figure>

## Exclude the interface itself in the context
??? example "Exclude the interface in the Interface Context"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("fbb7f735-3c1f-48de-9791-179d35ca7b98").context_diagram
    diag.render("svgdiagram", include_interface=False).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Interface Context of Interface-hide-interface.svg" width="1000000">
        <figcaption>Interface context diagram of `Interface` Logical ComponentExchange with type [LAB]</figcaption>
    </figure>

## Hide functional model elements from the context
??? example "Hide functions and functional exchanges in the Interface Context"

    ``` py
    import capellambse

    model = capellambse.MelodyModel("tests/data/ContextDiagram.aird")
    diag = model.by_uuid("fbb7f735-3c1f-48de-9791-179d35ca7b98").context_diagram
    diag.render("svgdiagram", hide_functions=True).save(pretty=True)
    ```
    <figure markdown>
        <img src="../assets/images/Interface Context of Interface-hide-functions.svg" width="1000000">
        <figcaption>Interface context diagram of `Interface` Logical ComponentExchange with type [LAB]</figcaption>
    </figure>

!!! warning "Interface context only supported for System and Logical ComponentExchanges"
