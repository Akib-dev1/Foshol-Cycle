"use client";

import L from "leaflet";
import { useEffect, useRef } from "react";
import boundaries from "@/data/bangladeshBoundaries.json";
import districts from "@/data/bangladeshDistricts.json";

const districtsById = new Map(districts.map((district) => [district.id, district]));
const padding = L.point(22, 22);
const pinIcon = L.divIcon({
  className: "bangladesh-map-pin",
  html: '<svg viewBox="0 0 26 34" width="26" height="34" aria-hidden="true"><path d="M13 32S2 20 2 13a11 11 0 0 1 22 0c0 7-11 19-11 19Z" fill="#163d2b" stroke="white" stroke-width="2"/><circle cx="13" cy="13" r="4" fill="white"/></svg>',
  iconSize: [26, 34],
  iconAnchor: [13, 32],
});

export default function BangladeshMap({ selection, onSelect }) {
  const containerRef = useRef(null);
  const viewRef = useRef(null);

  useEffect(() => {
    const map = L.map(containerRef.current, {
      scrollWheelZoom: false,
      zoomSnap: 0.25,
      maxZoom: 12,
      maxBoundsViscosity: 1,
    });
    const districtLayers = new Map();
    const boundaryLayer = L.geoJSON(boundaries, {
      style: ({ properties }) => ({
        className: "bangladesh-map-district",
        color: "#6f8d76",
        weight: 1,
        fillColor: districtsById.get(properties.id).isRajshahiDivision ? "#69a47a" : "#d9e6d9",
        fillOpacity: 1,
      }),
      onEachFeature(feature, layer) {
        const { id } = feature.properties;
        const label = document.createElement("span");
        label.textContent = districtsById.get(id).name;
        layer.bindTooltip(label, { sticky: true });
        layer.on("click", ({ latlng }) => {
          layer.closeTooltip();
          onSelect(id, latlng.lat, latlng.lng);
        });
        districtLayers.set(id, layer);
      },
    }).addTo(map);

    const bounds = boundaryLayer.getBounds();
    map.setMaxBounds(bounds.pad(0.15));
    map.fitBounds(bounds, { padding, animate: false });
    map.setMinZoom(map.getZoom());
    const marker = L.marker(bounds.getCenter(), {
      icon: pinIcon,
      interactive: false,
      keyboard: false,
    });
    viewRef.current = { map, marker, boundaryLayer, districtLayers, selectedLayer: null };

    const resizeObserver = new ResizeObserver(() => {
      const wasAtOverview = map.getZoom() === map.getMinZoom();
      map.invalidateSize({ animate: false });
      const overviewZoom = map.getBoundsZoom(bounds, false, padding.multiplyBy(2));
      map.setMinZoom(overviewZoom);
      if (wasAtOverview) map.fitBounds(bounds, { padding, animate: false });
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      viewRef.current = null;
    };
  }, [onSelect]);

  useEffect(() => {
    const view = viewRef.current;
    const { districtId, latitude, longitude } = selection.location;
    const point = [latitude, longitude];

    if (view.selectedLayer) view.boundaryLayer.resetStyle(view.selectedLayer);
    const districtLayer = view.districtLayers.get(districtId);
    districtLayer.setStyle({ color: "#163d2b", weight: 2.5 }).bringToFront();
    view.selectedLayer = districtLayer;
    view.marker.setLatLng(point).addTo(view.map);

    if (selection.revealPin) {
      view.map.panInside(point, { padding: L.point(44, 44), animate: false });
    }
  }, [selection, onSelect]);

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label="Interactive district map of Bangladesh"
      className="bangladesh-map h-[26rem] sm:h-[32rem]"
    />
  );
}
