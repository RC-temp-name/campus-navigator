
document.addEventListener("DOMContentLoaded", () => {
    if (!window.routeCoordinates || !window.floorBounds) {
        console.error("routeCoordinates or floorBounds missing from template");
        return;
    }

    // Initialize map with simple CRS
    const map = L.map("map", {
        crs: L.CRS.Simple,
        minZoom: -2,
        maxZoom: 4,
        zoomControl: true
    });

    // Bounds based on floor dimensions (feet)
    const bounds = [
        [0, 0],
        [floorBounds.height, floorBounds.width]
    ];

    map.fitBounds(bounds);

    // Draw 10ft grid
    function drawGrid() {
        const gridSize = 10;

        // Vertical lines
        for (let x = 0; x <= floorBounds.width; x += gridSize) {
            L.polyline([[0, x], [floorBounds.height, x]], {
                color: "#cccccc",
                weight: 1,
                opacity: 0.4
            }).addTo(map);
        }

        // Horizontal lines
        for (let y = 0; y <= floorBounds.height; y += gridSize) {
            L.polyline([[y, 0], [y, floorBounds.width]], {
                color: "#cccccc",
                weight: 1,
                opacity: 0.4
            }).addTo(map);
        }
    }

    drawGrid();

    // Convert backend coordinates → Leaflet [lat, lng]
    const latlngs = routeCoordinates.map(c => [c.y, c.x]);

    // Draw animated route line
    const routeLine = L.polyline(latlngs, {
        color: "blue",
        weight: 4,
        dashArray: "10, 10",
        className: "animated-route"
    }).addTo(map);

    // Fit map to route
    map.fitBounds(routeLine.getBounds(), { padding: [20, 20] });

    // Start + end markers
    if (latlngs.length > 0) {
        // Start marker (green)
        L.circleMarker(latlngs[0], {
            radius: 6,
            color: "green",
            fillColor: "green",
            fillOpacity: 1
        }).addTo(map);

        // End marker (red)
        L.circleMarker(latlngs[latlngs.length - 1], {
            radius: 6,
            color: "red",
            fillColor: "red",
            fillOpacity: 1
        }).addTo(map);
    }

    // Mobile responsiveness
    function resizeMap() {
        map.invalidateSize();
    }

    window.addEventListener("resize", resizeMap);
    setTimeout(resizeMap, 200);
});
