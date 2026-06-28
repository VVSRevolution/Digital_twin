import GeoJSON from "ol/format/GeoJSON"
import Style from "ol/style/Style"
import Stroke from "ol/style/Stroke"
import type Feature from "ol/Feature"
import type VectorSource from "ol/source/Vector"
import * as turf from "@turf/turf"

const format = new GeoJSON()

export function drawBuffers(feature: Feature, vectorSource: VectorSource) {

    const geojson = format.writeFeatureObject(feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326"
    })


    const distances = [90, 180, 270, 360, 450]

    distances.forEach((distance) => {
        const buffer = turf.buffer(geojson as any, distance, {
            units: "meters"
        })

        const bufferFeature = format.readFeature(buffer, {
            dataProjection: "EPSG:4326",
            featureProjection: "EPSG:3857"
        }) as Feature

        bufferFeature.setStyle(
            new Style({
                stroke: new Stroke({
                    color: "#0066ff",
                    width: 2
                })
            })
        )

        vectorSource.addFeature(bufferFeature)
    })
}