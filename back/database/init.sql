-- ============================================================
-- EXTENSÕES
-- ============================================================
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- TABELA DE SATELLITE_SOURCES
-- ============================================================
CREATE TABLE satellite_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    platform VARCHAR(50),
    sensor VARCHAR(50),
    band_thermal VARCHAR(10),
    resolution_m INTEGER,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO satellite_sources (name, description, platform, sensor, band_thermal, resolution_m) VALUES
    ('LANDSAT_8', 'Landsat 8 OLI/TIRS', 'Landsat', 'OLI/TIRS', 'Band 10', 30),
    ('LANDSAT_9', 'Landsat 9 OLI-2/TIRS-2', 'Landsat', 'OLI-2/TIRS-2', 'Band 10', 30);

-- ============================================================
-- TABELA DE PARKS
-- ============================================================
CREATE TABLE parks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    osm_id VARCHAR(50) UNIQUE,
    geometry GEOMETRY(POLYGON, 4326),
    centroid GEOMETRY(POINT, 4326),
    area_ha FLOAT,
    tags JSONB,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABELA DE COOLING_ANALYSES
-- ============================================================
CREATE TABLE cooling_analyses (
    id SERIAL PRIMARY KEY,
    park_id INTEGER NOT NULL REFERENCES parks(id) ON DELETE CASCADE,
    satellite_id INTEGER NOT NULL REFERENCES satellite_sources(id),
    image_date DATE NOT NULL,
    scene_id VARCHAR(100),
    cloud_cover FLOAT,
    pci FLOAT,
    pcd FLOAT,
    pca_ha FLOAT,
    pca_m2 FLOAT,
    park_lst_celsius FLOAT,
    park_lst_kelvin FLOAT,
    buffer_config JSONB,
    buffers_data JSONB,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ditto_thing_id VARCHAR(255),
    ditto_updated BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX idx_parks_geometry ON parks USING GIST (geometry);
CREATE INDEX idx_parks_centroid ON parks USING GIST (centroid);
CREATE INDEX idx_analyses_park_id ON cooling_analyses(park_id);
CREATE INDEX idx_analyses_satellite_id ON cooling_analyses(satellite_id);
CREATE INDEX idx_analyses_image_date ON cooling_analyses(image_date);
CREATE INDEX idx_analyses_analyzed_at ON cooling_analyses(analyzed_at DESC);

-- ============================================================
-- FUNÇÕES
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS .\database\
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
.\database\ language 'plpgsql';

CREATE TRIGGER update_parks_updated_at 
    BEFORE UPDATE ON parks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_satellite_updated_at 
    BEFORE UPDATE ON satellite_sources 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
