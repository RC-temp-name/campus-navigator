import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { loadMapScript } from "./harness.mjs";

const template = readFileSync(
  new URL("../../app/templates/index.html", import.meta.url),
  "utf8",
);

test("map stops with a useful error when template globals are missing", () => {
  const cases = [
    {
      name: "routeCoordinates",
      options: { floorBounds: { width: 30, height: 20 } },
    },
    { name: "floorBounds", options: { routeCoordinates: [{ x: 2, y: 3 }] } },
  ];

  for (const { name, options } of cases) {
    const harness = loadMapScript(options);

    assert.equal(harness.maps.length, 0, `${name} should prevent map setup`);
    assert.equal(
      harness.layers.length,
      0,
      `${name} should prevent layer setup`,
    );
    assert.deepEqual(harness.consoleMessages.error, [
      ["routeCoordinates or floorBounds missing from template"],
    ]);
  }
});

test("map template wires data globals before loading the browser scripts", () => {
  const directionsDataIndex = template.indexOf("const directionSteps");
  const directionsScriptIndex = template.indexOf("js/directions.js");
  const mapDataIndex = template.indexOf("window.routeCoordinates");
  const mapScriptIndex = template.indexOf("js/map.js");

  assert.match(template, /id="directions-card-container"/);
  assert.match(
    template,
    /const directionSteps\s*=\s*\{\{\s*steps\s*\|\s*tojson/,
  );
  assert.match(template, /id="map"/);
  assert.match(
    template,
    /window\.routeCoordinates\s*=\s*\{\{\s*coordinates\s*\|\s*tojson/,
  );
  assert.match(
    template,
    /window\.floorBounds\s*=\s*\{\{\s*floor_bounds\s*\|\s*tojson/,
  );
  assert.ok(directionsDataIndex >= 0);
  assert.ok(directionsDataIndex < directionsScriptIndex);
  assert.ok(mapDataIndex >= 0);
  assert.ok(mapDataIndex < mapScriptIndex);
});

test("map stops when Leaflet is missing", () => {
  const harness = loadMapScript({
    routeCoordinates: [{ x: 2, y: 3, floor: 1 }],
    floorBounds: { width: 30, height: 20 },
    globals: { L: undefined },
  });

  assert.equal(harness.maps.length, 0);
  assert.deepEqual(harness.consoleMessages.error, [
    ["Leaflet is missing from the page"],
  ]);
});

test("map declines to draw a route that crosses floors", () => {
  const harness = loadMapScript({
    routeCoordinates: [
      { x: 2, y: 3, floor: 1 },
      { x: 4, y: 5, floor: 2 },
    ],
    floorBounds: { width: 30, height: 20 },
  });

  assert.equal(harness.maps.length, 0);
  assert.deepEqual(harness.consoleMessages.error, [
    ["Map preview only supports routes on one floor"],
  ]);
});

test("map creates the bounded map without a route for empty coordinates", () => {
  const harness = loadMapScript({
    routeCoordinates: [],
    floorBounds: { width: 30, height: 20 },
  });

  assert.equal(harness.maps.length, 1);
  assert.equal(
    harness.layers.filter((layer) => layer.type === "polyline").length,
    7,
  );
  assert.equal(
    harness.layers.filter((layer) => layer.type === "circleMarker").length,
    0,
  );
  assert.equal(harness.maps[0].fitBoundsCalls.length, 1);
});

test("map uses Simple CRS, configured zoom options, and floor bounds", () => {
  const harness = loadMapScript({
    routeCoordinates: [
      { x: 4, y: 2 },
      { x: 28, y: 18 },
    ],
    floorBounds: { width: 30, height: 20 },
  });
  const map = harness.maps[0];

  assert.equal(map.container, "map");
  assert.equal(map.options.crs, harness.L.CRS.Simple);
  assert.deepEqual(
    {
      minZoom: map.options.minZoom,
      maxZoom: map.options.maxZoom,
      zoomControl: map.options.zoomControl,
    },
    { minZoom: -2, maxZoom: 4, zoomControl: true },
  );
  assert.deepEqual(map.fitBoundsCalls[0].bounds, [
    [0, 0],
    [20, 30],
  ]);
});

test("map draws a 10-foot grid across the floor dimensions", () => {
  const harness = loadMapScript({
    routeCoordinates: [{ x: 5, y: 5 }],
    floorBounds: { width: 30, height: 20 },
  });
  const grid = harness.layers.filter(
    (layer) => layer.type === "polyline" && layer.options.color === "#cccccc",
  );
  const map = harness.maps[0];

  assert.deepEqual(
    grid.map((layer) => layer.points),
    [
      [
        [0, 0],
        [20, 0],
      ],
      [
        [0, 10],
        [20, 10],
      ],
      [
        [0, 20],
        [20, 20],
      ],
      [
        [0, 30],
        [20, 30],
      ],
      [
        [0, 0],
        [0, 30],
      ],
      [
        [10, 0],
        [10, 30],
      ],
      [
        [20, 0],
        [20, 30],
      ],
    ],
  );
  assert.equal(grid.length, 7);
  assert.ok(grid.every((layer) => layer.map === map));
  assert.ok(
    grid.every(
      (layer) => layer.options.weight === 1 && layer.options.opacity === 0.4,
    ),
  );
});

test("map converts backend x/y points and styles the route line", () => {
  const harness = loadMapScript({
    routeCoordinates: [
      { x: 12, y: 4 },
      { x: 20, y: 15 },
    ],
    floorBounds: { width: 30, height: 20 },
  });
  const routeLine = harness.layers.find(
    (layer) =>
      layer.type === "polyline" && layer.options.className === "animated-route",
  );
  const routeFit = harness.maps[0].fitBoundsCalls[1];

  assert.equal(routeLine.map, harness.maps[0]);
  assert.deepEqual(routeLine.points, [
    [4, 12],
    [15, 20],
  ]);
  assert.deepEqual(routeLine.options, {
    color: "blue",
    weight: 4,
    dashArray: "10, 10",
    className: "animated-route",
  });
  assert.deepEqual(routeFit.bounds.toArray(), [
    [4, 12],
    [15, 20],
  ]);
  assert.deepEqual(routeFit.options, { padding: [20, 20] });
});

test("map marks the route start green and end red", () => {
  const harness = loadMapScript({
    routeCoordinates: [
      { x: 3, y: 7 },
      { x: 22, y: 11 },
    ],
    floorBounds: { width: 30, height: 20 },
  });
  const markers = harness.layers.filter(
    (layer) => layer.type === "circleMarker",
  );

  assert.equal(markers.length, 2);
  assert.equal(markers[0].map, harness.maps[0]);
  assert.deepEqual(markers[0].points, [7, 3]);
  assert.deepEqual(markers[0].options, {
    radius: 6,
    color: "green",
    fillColor: "green",
    fillOpacity: 1,
  });
  assert.deepEqual(markers[1].points, [11, 22]);
  assert.deepEqual(markers[1].options, {
    radius: 6,
    color: "red",
    fillColor: "red",
    fillOpacity: 1,
  });
});

test("map invalidates its size on the resize event and deferred startup check", () => {
  const harness = loadMapScript({
    routeCoordinates: [{ x: 5, y: 5 }],
    floorBounds: { width: 30, height: 20 },
  });
  const map = harness.maps[0];

  assert.equal(harness.window.listenerCount("resize"), 1);
  assert.equal(map.invalidateSizeCalls, 1);

  harness.dispatchWindowEvent("resize");
  assert.equal(map.invalidateSizeCalls, 2);
});
