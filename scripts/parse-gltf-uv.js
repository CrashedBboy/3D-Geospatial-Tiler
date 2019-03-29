const fs = require('fs')
const path = require('path')

const VERTEX_PER_FACE = 3;

const GLTF_PATH = '../models/mountain-gltf/tile4/model.gltf';

let absoluteGltfPath = path.resolve(path.join(__dirname, GLTF_PATH));

let gltf = JSON.parse(fs.readFileSync(absoluteGltfPath, 'utf8'));

let output = {
    gltf: path.basename(absoluteGltfPath),
    maps: []
}

if (gltf && gltf.scene) {

    console.log('cannot parse gltf file or scene');
    process.exit();
}

let primitiveUVMaps = new Array();

gltf.scenes[gltf.scene].nodes.forEach((nodeIndex) => {
    let node = gltf.nodes[nodeIndex];
    let nodeMesh = gltf.meshes[node.mesh];
    let nodeMeshPrimitives = nodeMesh.primitives;

    nodeMeshPrimitives.forEach((primitive) => {
        let primitiveMaterial = gltf.materials[primitive.material];

        if (primitiveMaterial.pbrMetallicRoughness) {
            if (primitiveMaterial.pbrMetallicRoughness.baseColorTexture) {
                primitiveUVMaps.push({
                    uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.pbrMetallicRoughness.baseColorTexture.texCoord]],
                    image: gltf.images[gltf.textures[primitiveMaterial.pbrMetallicRoughness.baseColorTexture.index].source]
                });
            }

            if (primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture) {
                primitiveUVMaps.push({
                    uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture.texCoord]],
                    image: gltf.images[gltf.textures[primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture.index].source]
                });
            }
        }

        if (primitiveMaterial.normalTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.normalTexture.texCoord]],
                image: gltf.images[gltf.textures[primitiveMaterial.normalTexture.index].source]
            });
        }

        if (primitiveMaterial.occlusionTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.occlusionTexture.texCoord]],
                image: gltf.images[gltf.textures[primitiveMaterial.occlusionTexture.index].source]
            });
        }

        if (primitiveMaterial.emissiveTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.emissiveTexture.texCoord]],
                image: gltf.images[gltf.textures[primitiveMaterial.emissiveTexture.index].source]
            });
        }
    });
});

console.log(primitiveUVMaps);

if (primitiveUVMaps.length == 0) {
    console.log('no mapped texture images found');
    process.exit();
}

primitiveUVMaps.forEach((map) => {
    let mapBufferView = gltf.bufferViews[map.uvAccessor.bufferView];

    let bufferPath = path.resolve( path.join(path.dirname(absoluteGltfPath), gltf.buffers[mapBufferView.buffer].uri) );

    let geometryBuffer = fs.readFileSync(bufferPath);

    // assume that all elements in uv maps are VEC2 : 5126 (FLOAT)
    if (map.uvAccessor.componentType != 5126 || map.uvAccessor.type != "VEC2") {
        console.log('this map is not using float values to map image textures');
        return;
    }

    uvs = new Array();

    for (let i = 0; i < map.uvAccessor.count; i++) {
        let u = geometryBuffer.readFloatLE(mapBufferView.byteOffset + 2*i*4);
        let v = geometryBuffer.readFloatLE(mapBufferView.byteOffset + 2*(i+1)*4);
        uvs.push([u, v]);
    }

    faceUvs = new Array();
    for (let i = 0; i < (uvs.length / VERTEX_PER_FACE); i++) {
        faceUvs.push([uvs[3*i], uvs[3*i+1], uvs[3*i+2]]);
    }

    console.log(faceUvs.length);

    output.maps.push({
        image: map.image,
        faceUvs: faceUvs
    });
});

fs.writeFileSync(path.join(path.dirname(absoluteGltfPath), 'uv_coord.json'), JSON.stringify(output, null, 2), { encoding: 'utf8' });