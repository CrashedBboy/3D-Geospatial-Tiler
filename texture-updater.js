const fs = require('fs');
const path = require('path');
const argv = require('yargs').argv;

if (!argv.input || !fs.existsSync(argv.input)) {
    console.log('input file not found');
    process.exit(1);
}

let absoluteGltfPath = path.resolve(argv.input);
let absoluteMapPath = path.join( path.dirname(absoluteGltfPath) , "refined_texture_map.json");

if (!fs.existsSync(absoluteMapPath)) {
    console.log("MAP file is missing");
    process.exit(1);
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

process.exit(0);