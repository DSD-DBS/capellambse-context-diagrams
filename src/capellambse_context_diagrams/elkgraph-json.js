/*******************************************************************************
 * SPDX-FileCopyrightText: Copyright (c) 2021 Kiel University and others.
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0.
 *
 * SPDX-License-Identifier: EPL-2.0
 *******************************************************************************/
"use strict";
exports.__esModule = true;
exports.isExtended = exports.isPrimitive = void 0;
function isPrimitive(edge) {
    return edge.source !== undefined && edge.target !== undefined;
}
exports.isPrimitive = isPrimitive;
function isExtended(edge) {
    return edge.sources !== undefined && edge.targets !== undefined;
}
exports.isExtended = isExtended;
