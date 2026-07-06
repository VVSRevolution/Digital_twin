export async function searchPark(query: string) {
    const overpassQuery = `
    [out:json];
    (
      way["leisure"="park"]["name"~"${query}", i];
      relation["leisure"="park"]["name"~"${query}", i];
    );
    out geom;
  `

    const res = await fetch("https://overpass-api.de/api/interpreter", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: new URLSearchParams({
            data: overpassQuery
        })
    })

    return await res.json()
}
//
// export async function searchPark(query: string) {
//     const res = {
//         version: 0.6,
//         elements: [
//             {
//                 type: "way",
//                 id: 159590062,
//                 geometry: [
//                     {lat: -16.7088102, lon: -49.2726366},
//                     {lat: -16.7112558, lon: -49.2708214},
//                     {lat: -16.7112546, lon: -49.2705297},
//                     {lat: -16.7112236, lon: -49.2694104},
//                     {lat: -16.7111605, lon: -49.2693521},
//                     {lat: -16.7096386, lon: -49.2694267},
//                     {lat: -16.7095146, lon: -49.2694926},
//                     {lat: -16.7094656, lon: -49.2695489},
//                     {lat: -16.7078516, lon: -49.2711730},
//                     {lat: -16.7079009, lon: -49.2712490},
//                     {lat: -16.7079058, lon: -49.2712568},
//                     {lat: -16.7084674, lon: -49.2721348},
//                     {lat: -16.7088102, lon: -49.2726366}
//                 ],
//                 tags: {
//                     leisure: "park",
//                     name: "Parque Vaca Brava"
//                 }
//             }
//         ]
//     }
//
//     return res
// }