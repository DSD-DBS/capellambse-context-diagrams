<!--
 ~ SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
 ~ SPDX-License-Identifier: Apache-2.0
 -->

# Custom Diagram

`Custom diagram`s let's you create custom diagrams based on the data in the model. You define the data collection using a dictionary.
You can access `.custom_diagram` on any supported model element.

## Collector definition

### `get` and `include`

At every step of the collection, you can either `get` or `include` elements. `get` will simply get the element and `include` will include the element in the collection. `name` is the attribute name.

```yaml
get:
    - name: inputs
    include:
        - name: exchanges
        - name: links
    - name: outputs
    include:
        - name: exchanges
        - name: links
    - name: ports
    include:
        - name: exchanges
        - name: links
```

In the example above, we first `get` all the inputs of our target element and iterate over them. For each input, we include all the exchanges and links in the resulting diagram. We do the same for outputs and ports. Note that `get` does not include the element in the diagram, it just gets the element, but calling `include` on an edge will also include the edge's source and target ports.

### `filter`

Whenever you have a list of elements and you want to filter them, you can use the `filter` keyword. The `filter` keyword takes a dictionary as an argument. The dictionary should have the key as the attribute name and the value as the value you want to filter on.

```yaml
get:
    - name: inputs
      include:
          - name: exchanges
            filter:
                kind: "FunctionalExchange"
```

In the example above, we get all the inputs of our target element and include all the exchanges that are of kind `FunctionalExchange` in the resulting diagram.

### `repeat`

With the `repeat` keyword, you can repeat the collection. The value of `repeat` should be an integer. If the value is -1, the collection will repeat until no new elements are found. If the value is 0, the collection will not repeat. If the value is 1, the collection will repeat once and so on.

```yaml
repeat: -1
get:
    - name: source
    include:
        name: links
    - name: target
    include:
        name: links
```

In the example above, we get the source and target of our target element and include all the links in the resulting diagram. For each link we again get the source and target and include all the links in the resulting diagram. This will repeat until no new elements are found.

## API Usage

```python
import capellambse
import yaml

my_model = capellambse.MelodyModel(...)
my_element = my_model.by_uuid(...)
my_yaml = "..."

my_element.custom_diagram(collect=yaml.safe_load(my_yaml)).render("svgdiagram").save(pretty=True)
```

## Supported Elements

-   [`sa.SystemFunction`][capellambse.metamodel.sa.SystemFunction]
-   [`cs.PhysicalLink`][capellambse.metamodel.cs.PhysicalFunction]
-   [`la.LogicalFunction`][capellambse.metamodel.la.LogicalFunction]
-   [`pa.PhysicalFunction`][capellambse.metamodel.pa.PhysicalFunction]
-   [`fa.ComponentExchange`][capellambse.metamodel.fa.ComponentExchange]
-   [`cs.PhysicalPort`][capellambse.metamodel.cs.PhysicalPort]

## Check out the code

To understand the collection have a look into the
[`cable_tree`][capellambse_context_diagrams.collectors.cable_tree]
module.
