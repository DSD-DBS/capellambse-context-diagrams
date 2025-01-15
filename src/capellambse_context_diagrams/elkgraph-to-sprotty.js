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
exports.ElkGraphJsonToSprotty = void 0;
var elkgraph_json_1 = require("./elkgraph-json");
var ElkGraphJsonToSprotty = /** @class */ (function () {
  function ElkGraphJsonToSprotty() {
    this.nodeIds = new Set();
    this.edgeIds = new Set();
    this.portIds = new Set();
    this.labelIds = new Set();
    this.sectionIds = new Set();
  }
  ElkGraphJsonToSprotty.prototype.transform = function (elkGraph) {
    var _a, _b;
    var _this = this;
    var sGraph = {
      type: "graph",
      id: elkGraph.id || "root",
      children: [],
    };
    if (elkGraph.children) {
      var children = elkGraph.children.map(function (n) {
        return _this.transformElkNode(n);
      });
      (_a = sGraph.children).push.apply(_a, children);
    }
    if (elkGraph.edges) {
      var sEdges = elkGraph.edges.map(function (e) {
        return _this.transformElkEdge(e);
      });
      (_b = sGraph.children).push.apply(_b, sEdges);
    }
    return sGraph;
  };
  ElkGraphJsonToSprotty.prototype.transformElkNode = function (elkNode) {
    var _a, _b, _c, _d;
    var _this = this;
    this.checkAndRememberId(elkNode, this.nodeIds);
    var sNode = {
      type: "node",
      id: elkNode.id,
      position: this.pos(elkNode),
      size: this.size(elkNode),
      children: [],
    };
    // children
    if (elkNode.children) {
      var sNodes = elkNode.children.map(function (n) {
        return _this.transformElkNode(n);
      });
      (_a = sNode.children).push.apply(_a, sNodes);
    }
    // ports
    if (elkNode.ports) {
      var sPorts = elkNode.ports.map(function (p) {
        return _this.transformElkPort(p);
      });
      (_b = sNode.children).push.apply(_b, sPorts);
    }
    // labels
    if (elkNode.labels) {
      var sLabels = elkNode.labels
        .filter(function (l) {
          return l.text !== undefined;
        })
        .map(function (l) {
          return _this.transformElkLabel(l);
        });
      (_c = sNode.children).push.apply(_c, sLabels);
    }
    // edges
    if (elkNode.edges) {
      var sEdges = elkNode.edges.map(function (e) {
        return _this.transformElkEdge(e);
      });
      (_d = sNode.children).push.apply(_d, sEdges);
    }
    return sNode;
  };
  ElkGraphJsonToSprotty.prototype.transformElkPort = function (elkPort) {
    var _a;
    var _this = this;
    this.checkAndRememberId(elkPort, this.portIds);
    var sPort = {
      type: "port",
      id: elkPort.id,
      position: this.pos(elkPort),
      size: this.size(elkPort),
      children: [],
    };
    // labels
    if (elkPort.labels) {
      var sLabels = elkPort.labels
        .filter(function (l) {
          return l.text !== undefined;
        })
        .map(function (l) {
          return _this.transformElkLabel(l);
        });
      (_a = sPort.children).push.apply(_a, sLabels);
    }
    return sPort;
  };
  ElkGraphJsonToSprotty.prototype.transformElkLabel = function (elkLabel) {
    // For convenience, and since labels do not have to be referenced by other elements,
    // we allow their ids to be generated on-the-fly
    this.checkAndRememberId(elkLabel, this.labelIds, true);
    return {
      type: "label",
      id: elkLabel.id,
      text: elkLabel.text,
      position: this.pos(elkLabel),
      size: this.size(elkLabel),
    };
  };
  /**
   * Due to ELK issue #553 the computed layout of primitive edges is not transferred
   * back in the correct way. Instead of using the primitive edge format the edge sections
   * of the extended edge format are returned.
   */
  ElkGraphJsonToSprotty.prototype.isBugged = function (elkEdge) {
    return elkEdge.sections !== undefined && elkEdge.sections.length > 0;
  };
  ElkGraphJsonToSprotty.prototype.transferSectionBendpoints = function (
    section,
    sEdge
  ) {
    var _a;
    this.checkAndRememberId(section, this.sectionIds);
    sEdge.routingPoints.push(section.startPoint);
    if (section.bendPoints) {
      (_a = sEdge.routingPoints).push.apply(_a, section.bendPoints);
    }
    sEdge.routingPoints.push(section.endPoint);
  };
  ElkGraphJsonToSprotty.prototype.transformElkEdge = function (elkEdge) {
    var _a, _b;
    var _this = this;
    this.checkAndRememberId(elkEdge, this.edgeIds);
    var sEdge = {
      type: "edge",
      id: elkEdge.id,
      sourceId: "",
      targetId: "",
      routingPoints: [],
      children: [],
    };
    if (elkgraph_json_1.isPrimitive(elkEdge)) {
      sEdge.sourceId = elkEdge.source;
      sEdge.targetId = elkEdge.target;
      // Workaround for ELK issue #553
      if (this.isBugged(elkEdge)) {
        var section = elkEdge.sections[0];
        this.transferSectionBendpoints(section, sEdge);
      } else {
        if (elkEdge.sourcePoint) sEdge.routingPoints.push(elkEdge.sourcePoint);
        if (elkEdge.bendPoints)
          (_a = sEdge.routingPoints).push.apply(_a, elkEdge.bendPoints);
        if (elkEdge.targetPoint) sEdge.routingPoints.push(elkEdge.targetPoint);
      }
    } else if (elkgraph_json_1.isExtended(elkEdge)) {
      sEdge.sourceId = elkEdge.sources[0];
      sEdge.targetId = elkEdge.targets[0];
      if (elkEdge.sections) {
        elkEdge.sections.forEach(function (section) {
          return _this.transferSectionBendpoints(section, sEdge);
        });
      }
    }
    if (elkEdge.junctionPoints) {
      elkEdge.junctionPoints.forEach(function (jp, i) {
        var sJunction = {
          type: "junction",
          id: elkEdge.id + "_j" + i,
          position: jp,
        };
        sEdge.children.push(sJunction);
      });
    }
    if (elkEdge.labels) {
      var sLabels = elkEdge.labels
        .filter(function (l) {
          return l.text !== undefined;
        })
        .map(function (l) {
          return _this.transformElkLabel(l);
        });
      (_b = sEdge.children).push.apply(_b, sLabels);
    }
    return sEdge;
  };
  ElkGraphJsonToSprotty.prototype.pos = function (elkShape) {
    return { x: elkShape.x || 0, y: elkShape.y || 0 };
  };
  ElkGraphJsonToSprotty.prototype.size = function (elkShape) {
    return { width: elkShape.width || 0, height: elkShape.height || 0 };
  };
  ElkGraphJsonToSprotty.prototype.checkAndRememberId = function (
    e,
    set,
    generateIdIfRequired
  ) {
    if (generateIdIfRequired === void 0) {
      generateIdIfRequired = false;
    }
    if (e.id === undefined) {
      if (generateIdIfRequired) {
        do {
          e.id = this.generateRandomId();
        } while (set.has(e.id));
      } else {
        throw Error("An element is missing an id.");
      }
    }
    if (set.has(e.id)) {
      throw Error("Duplicate id: " + e.id + ".");
    } else {
      set.add(e.id);
    }
  };
  ElkGraphJsonToSprotty.prototype.generateRandomId = function (length) {
    if (length === void 0) {
      length = 6;
    }
    var random = Math.random() * (Math.pow(10, length) - 1);
    var padded = Math.floor(random) + "";
    while (padded.length < length) {
      padded = "0" + padded;
    }
    return "g_" + padded;
  };
  return ElkGraphJsonToSprotty;
})();
exports.ElkGraphJsonToSprotty = ElkGraphJsonToSprotty;
