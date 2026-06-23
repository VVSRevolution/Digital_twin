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