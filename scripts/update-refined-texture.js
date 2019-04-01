const fs = require('fs');
const path = require('path');

const GLTF_PATH = '../models/mountain-gltf/tile1/refined/model.gltf';
const MAP_PATH = '../models/mountain-gltf/tile1/refined/refined_texture_map.json';

let absoluteGltfPath = path.resolve(path.join(__dirname, GLTF_PATH));
let absoluteMapPath = path.resolve(path.join(__dirname, MAP_PATH));

if (!fs.existsSync(absoluteGltfPath) || !fs.existsSync(absoluteMapPath)) {
    console.log("GLTF or MAP file is missing");
    process.exit();
}

let map = JSON.parse(fs.readFileSync(absoluteMapPath, 'utf8'));
let gltf = JSON.parse(fs.readFileSync(absoluteGltfPath, 'utf8'));

map.forEach((m) => {

    // looking for old texture image name in gltf
    for (let i = 0; i < gltf.images.length; i++) {
        if (path.basename(gltf.images[i].uri) == m.old) {
            gltf.images[i].name = m.new;
            gltf.images[i].mimeType = 'image/jpeg';
            gltf.images[i].uri = path.dirname(gltf.images[i].uri) + '/' + m.new;
        }
    }
});

let absoluteOutputPath = path.join( path.dirname(absoluteGltfPath), "refined_" + path.basename(absoluteGltfPath));

fs.writeFileSync(absoluteOutputPath, JSON.stringify(gltf, null, 2));