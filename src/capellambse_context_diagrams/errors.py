# SPDX-FileCopyrightText: 2022 Copyright DB InfraGO AG and the capellambse-context-diagrams contributors
# SPDX-License-Identifier: Apache-2.0
"""Errors for capellambse_context_diagrams."""


class CapellambseError(Exception):
    """Error raised by capellambse."""


class CycleError(CapellambseError):
    """Error raised when a cycle is detected."""
