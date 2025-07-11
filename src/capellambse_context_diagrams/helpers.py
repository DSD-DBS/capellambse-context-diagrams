# SPDX-FileCopyrightText: Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0

from capellambse import model as m


def get_model_object(model: m.MelodyModel, uuid: str) -> m.ModelElement | None:
    """Try to return a Capella model element."""
    try:
        return model.by_uuid(uuid)
    except KeyError:
        return None


def has_same_type(obj1: m.ModelElement, obj2: m.ModelElement) -> bool:
    """Check if two model elements have the same type."""
    return type(obj1).__name__ == type(obj2).__name__
