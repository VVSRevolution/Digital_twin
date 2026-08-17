import GeoJSON from "ol/format/GeoJSON"
import Style from "ol/style/Style"
import Stroke from "ol/style/Stroke"
import type VectorSource from "ol/source/Vector"
import type OLFeature from "ol/Feature"
import * as turf from "@turf/turf"

const format = new GeoJSON()

/**
 * Desenha buffers concêntricos em torno de um parque
 * @param feature - Feature do parque (OpenLayers)
 * @param vectorSource - Fonte de vetores onde adicionar os buffers
 * @param numBuffers - Número de anéis (padrão: 11)
 * @param bufferDistance - Distância inicial em metros (padrão: 90)
 */
export function drawBuffers(
    feature: OLFeature,
    vectorSource: VectorSource,
    numBuffers: number = 11,
    bufferDistance: number = 90
) {
    // 🔥 REMOVE BUFFERS ANTIGOS (para não acumular)
    const features = vectorSource.getFeatures()
    const toRemove: OLFeature[] = []

    features.forEach((f: OLFeature) => {
        // 🔥 VERIFICA SE É UM BUFFER PELA PROPRIEDADE 'isBuffer'
        if (f.get('isBuffer') === true) {
            toRemove.push(f)
        }
    })

    toRemove.forEach((f: OLFeature) => {
        vectorSource.removeFeature(f)
    })

    // 🔥 CONVERTE FEATURE PARA GEOJSON
    const geojson = format.writeFeatureObject(feature, {
        featureProjection: "EPSG:3857",
        dataProjection: "EPSG:4326"
    })

    // 🔥 USA OS VALORES PASSADOS
    const distances: number[] = []
    for (let i = 1; i <= numBuffers; i++) {
        distances.push(bufferDistance * i)
    }

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
                    color: "#000000",
                    width: 2
                })
            })
        )

        olFeature.set('zIndex', 9)
        olFeature.set('isBuffer', true) // 🔥 MARCA COMO BUFFER

        vectorSource.addFeature(olFeature)
    }
}