<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB Netz AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Applying Capella filters

With release [`v0.4.11`](https://github.com/DSD-DBS/py-capellambse/releases/tag/v0.4.11) of [py-capellambse](https://github.com/DSD-DBS/py-capellambse)
you can apply filters headlessly. Since an instance of a [`ContextDiagram`][capellambse_context_diagrams.context.ContextDiagram] is not stored in
the `.aird` file of your Capella model there is no way to apply
filters via Capella/GUI. The [filters][capellambse_context_diagrams.filters] implementation bridge
the filter functionality of py-capellambse such that the labels are
adjusted without needing diagram elements from within the .aird file.

## Capella filters

Currently the supported filters are:

??? success "Show [`ExchangeItem`][capellambse.model.crosslayer.information.ExchangeItem]s"

    ```py
    from capellambse import MelodyModel
    from capellambse_context_diagrams import filters

    lost = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae")
    diag = obj.context_diagram
    assert filters.EX_ITEMS == "show.exchange.items.filter"
    diag.filters.add(filters.EX_ITEMS)
    diag.render("svgdiagram").save_drawing(True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of Lost ex.svg" width="1000000">
        <figcaption>Context diagram of Lost SystemFunction with applied filter [`EX_ITEMS_FILTER`][capellambse_context_diagrams.filters.EX_ITEMS]</figcaption>
    </figure>

??? success "Show [`FunctionalExchange`][capellambse.model.crosslayer.fa.FunctionalExchange]s and [`ExchangeItem`][capellambse.model.crosslayer.information.ExchangeItem]s"

    ```py
    from capellambse import MelodyModel
    from capellambse_context_diagrams import filters

    lost = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae")
    diag = obj.context_diagram
    assert filters.FEX_EX_ITEMS == "show.functional.exchanges.exchange.items.filter"
    filters.filters = {filters.FEX_EX_ITEMS}
    diag.render("svgdiagram").save_drawing(True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of Lost fex and ex.svg" width="1000000">
        <figcaption>Context diagram of Lost SystemFunction with applied filter [`FEX_EX_ITEMS_FILTER`][capellambse_context_diagrams.filters.FEX_EX_ITEMS]</figcaption>
    </figure>

## Custom filters

??? tip "Custom Filter - Show [`FunctionalExchange`][capellambse.model.crosslayer.fa.FunctionalExchange]s **or** [`ExchangeItem`][capellambse.model.crosslayer.information.ExchangeItem]s"

    ```py
    from capellambse import MelodyModel
    from capellambse_context_diagrams import filters

    lost = model.by_uuid("a5642060-c9cc-4d49-af09-defaa3024bae")
    diag = obj.context_diagram
    assert filters.FEX_OR_EX_ITEMS == "capellambse_context_diagrams-show.functional.exchanges.or.exchange.items.filter"
    filters.filters.add(filters.FEX_OR_EX_ITEMS)
    diag.render("svgdiagram").save_drawing(True)
    ```
    <figure markdown>
        <img src="../../assets/images/Context of Lost fex or ex.svg" width="1000000">
        <figcaption>Context diagram of Lost SystemFunction with applied filter [`FEX_OR_EX_ITEMS_FILTER`][capellambse_context_diagrams.filters.FEX_OR_EX_ITEMS]</figcaption>
    </figure>

Make sure to check out our [**Stylings**][capellambse_context_diagrams.styling] feature as well.
