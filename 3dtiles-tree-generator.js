const argv = require('yargs').argv;
const fs = require('fs');
const path = require('path');
const Cesium = require('cesium');
const ConvertGltfToGLB = require('gltf-import-export').ConvertGltfToGLB;
const glbToB3dm = require('./3d-tiles-tools/lib/glbToB3dm');

const MAX_GEO_ERROR = 3; // if MAX_GEO_ERROR = 4, max geometricError = 2^4 = 32 

let inputPath = argv.input;
let outputPath = argv.output;
let latitude = parseFloat(argv.latitude);
let longitude = parseFloat(argv.longitude);
let height = parseFloat(argv.height);

if (!inputPath || !fs.existsSync(inputPath) || !outputPath || !fs.existsSync(outputPath)) {
    console.log('input file / output directory not found');
    process.exit(1);
}

let tilesList = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

// build qual-tree hierarchy
let quadTree = {
    level: tilesList[0].total_level,
    root: null
};

// searching for root tile
for (let i = 0; i < tilesList.length; i++) {
    let tile = tilesList[i];
    if (tile.level == 0) {
        quadTree.root = { level: tile.level, x: tile.x, y: tile.y, gltf: getRefinedGltfPath(tile.gltf_path), children: [] };
        break;
    }
}

expandTree(quadTree.root, quadTree.level);

let tileset = {
    asset: {
        version: "1.0",
        tilesetVersion: "3d-tiler",
        gltfUpAxis: "Y"
    },
    geometricError: 200,
    root: {
        transform: getTransformation(latitude, longitude, height),
        boundingVolume: {
            region: getWorldBoundry(getObjectBoundry(quadTree.root.gltf), [latitude, longitude, height])
        },
        geometricError: getGeometricError(quadTree.root.level),
        refine: "REPLACE",
        content: {
            uri: getB3dmFilename(quadTree.root)
        },
        children: []
    }
};

gltfToB3dm(quadTree.root.gltf, getB3dmFilepath(quadTree.root, outputPath));

quadTree.root.children.forEach((ch) => {
    generateTile(tileset.root, ch);
});

fs.writeFileSync(path.join(outputPath, "tileset.json"), JSON.stringify(tileset));

function getRefinedGltfPath(gltfpath) {
    let dir = path.dirname(gltfpath);
    let basename = path.basename(gltfpath);

    let hasPrefix = path.join(dir, 'refined_' + basename);

    if (fs.existsSync(hasPrefix)) {
        return hasPrefix;
    } else {
        return gltfpath;
    }
}

function expandTree(node, totalLevel) {
    if (node.level == totalLevel) {
        return;
    }

    let gap = 2 ** (totalLevel - (node.level + 1));

    let searchInList = (tile, tilesList) => {
        for (let i = 0; i < tilesList.length; i++) {
            if (tile.level == tilesList[i].level && tile.x == tilesList[i].x && tile.y == tilesList[i].y) {
                return tilesList[i];
            }
        }
        return null;
    }

    let tile1 = searchInList({ level: node.level + 1, x: node.x, y: node.y }, tilesList);
    let tile2 = searchInList({ level: node.level + 1, x: node.x + gap, y: node.y }, tilesList);
    let tile3 = searchInList({ level: node.level + 1, x: node.x, y: node.y + gap }, tilesList);
    let tile4 = searchInList({ level: node.level + 1, x: node.x + gap, y: node.y + gap }, tilesList);

    tiles = [tile1, tile2, tile3, tile4];
    tiles.forEach((t) => {
        if (t) {
            let ch = {
                level: t.level,
                x: t.x,
                y: t.y,
                gltf: getRefinedGltfPath(t.gltf_path),
                children: []
            };
            node.children.push(ch);
        }
    });

    node.children.forEach((ch) => {
        expandTree(ch, totalLevel);
    });
};

// passed in degrees
function getTransformation(latitude, longitude, height) {

    latitudeRadian = latitude / (180 / Math.PI);
    longitudeRadian = longitude / (180 / Math.PI);

    return Cesium.Matrix4.toArray(
        Cesium.Transforms.headingPitchRollToFixedFrame(
            Cesium.Cartesian3.fromRadians(longitudeRadian, latitudeRadian, height),
            new Cesium.HeadingPitchRoll(0, 0, 0)
        ));
}

// get geometric max & min value of vertex positions
function getObjectBoundry(gltfPath) {
    let gltf = JSON.parse(fs.readFileSync(gltfPath));

    let xMax = Number.NEGATIVE_INFINITY;
    let xMin = Number.POSITIVE_INFINITY;
    let yMax = Number.NEGATIVE_INFINITY;
    let yMin = Number.POSITIVE_INFINITY;
    let zMax = Number.NEGATIVE_INFINITY;
    let zMin = Number.POSITIVE_INFINITY;

    if (!gltf.meshes) {
        return [xMax, xMin, yMax, yMin, zMax, zMin];
    }

    for (let i = 0; i < gltf.meshes.length; i++) {
        let m = gltf.meshes[i];

        m.primitives.forEach((p) => {
            let accessor = gltf.accessors[p.attributes.POSITION];

            // x
            if (accessor.min[0] < xMin) {
                xMin = accessor.min[0];
            }
            if (accessor.max[0] > xMax) {
                xMax = accessor.max[0];
            }

            // y
            if (accessor.min[1] < yMin) {
                yMin = accessor.min[1];
            }
            if (accessor.max[1] > yMax) {
                yMax = accessor.max[1];
            }

            // z
            if (accessor.min[2] < zMin) {
                zMin = accessor.min[2];
            }
            if (accessor.max[2] > zMax) {
                zMax = accessor.max[2];
            }
        });
    }

    return [xMax, xMin, yMax, yMin, zMax, zMin];
}

// assume all model are Y up, -Z forward
// boundry: [xMax, xMin, yMax, yMin, zMax, zMin]
// center: [latitude, longitude, height]
function getWorldBoundry(boundry, center) {

    // longitude in radians
    let metersToLongitude = (meters, latitude) => {
        return meters * 0.000000156785 / Math.cos(latitude);
    }

    // latitude in radians
    let metersToLatitude = (meters) => {
        return meters * 0.000000157891;
    }

    let lonMin = metersToLongitude(boundry[1], latitude / (180 / Math.PI));
    let lonMax = metersToLongitude(boundry[0], latitude / (180 / Math.PI));

    let latMin = metersToLatitude(boundry[4]); // greater z value: souther
    let latMax = metersToLatitude(boundry[5]);

    let centerLat = center[0] / (180 / Math.PI);
    let centerLon = center[1] / (180 / Math.PI);
    let centerHeight = center[2];

    return [
        centerLon + lonMin,
        centerLat - latMin,
        centerLon + lonMax,
        centerLat - latMax,
        centerHeight + boundry[3],
        centerHeight + boundry[2]
    ];
}

function getB3dmFilename(node) {
    return node.level + "_" + node.x + "_" + node.y + ".b3dm";
}

function getB3dmFilepath(node, outputPath) {
    return path.join(outputPath, getB3dmFilename(node));
}

function getGeometricError(level) {
    return 2 ** (MAX_GEO_ERROR - level);
}

function gltfToB3dm(gltfPath, b3dmPath) {
    let glbPath = gltfPath + '.glb';

    ConvertGltfToGLB(gltfPath, glbPath);

    let glbBuffer = fs.readFileSync(glbPath);

    // Set b3dm spec requirements
    let featureTableJson = {
        BATCH_LENGTH: 0
    };

    let b3dmBuffer = glbToB3dm(glbBuffer, featureTableJson);
    fs.writeFileSync(b3dmPath, b3dmBuffer);

    fs.unlinkSync(glbPath);
}

function generateTile(parentTile, node) {
    let tileset = {
        boundingVolume: {
            region: getWorldBoundry(getObjectBoundry(node.gltf), [latitude, longitude, height])
        },
        geometricError: getGeometricError(node.level),
        refine: "REPLACE",
        content: {
            uri: getB3dmFilename(node)
        },
        children: []
    };

    parentTile.children.push(tileset);

    gltfToB3dm(node.gltf, getB3dmFilepath(node, outputPath));

    node.children.forEach((ch) => {
        generateTile(tileset, ch);
    });
}

// test command: node .\3dtiles-generator.js --input "....\\blender-3d-tiler\\export\\mountain\\lod.json" --output ".....\\blender-3d-tiler\\export\\mountain\\3dtiles"