import GeoJSON from "ol/format/GeoJSON"
import Style from "ol/style/Style"
import Stroke from "ol/style/Stroke"
import type VectorSource from "ol/source/Vector"
import type OLFeature from "ol/Feature"
import * as turf from "@turf/turf"

const format = new GeoJSON()

export function drawBuffers(feature: OLFeature, vectorSource: VectorSource) {

    const geojson = format.writeFeatureObject(feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326"
    })

    const step = 90
    const distances = Array.from({length: 11}, (_, i) => (i + 1) * step)

    let prev: any = null

    for (const d of distances) {

        const outer = turf.buffer(geojson as any, d, {units: "meters"})

        let ring = outer

        if (prev) {
            const result = turf.difference(
                turf.featureCollection([outer as any, prev as any])
            )

            if (!result) {
                prev = outer
                continue
            }

            ring = result
        }

        prev = outer

        const olFeature = format.readFeature(ring, {
            dataProjection: "EPSG:4326",
            featureProjection: "EPSG:3857"
        }) as OLFeature

        olFeature.setStyle(
            new Style({
                stroke: new Stroke({
                    color: "#0066ff",
                    width: 2
                })
            })
        )

        vectorSource.addFeature(olFeature)
    }
}