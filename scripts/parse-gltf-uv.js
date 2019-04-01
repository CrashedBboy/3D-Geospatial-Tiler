const fs = require('fs')
const path = require('path')

const VERTEX_PER_FACE = 3;

const GLTF_PATH = '../models/mountain-gltf/tile1/model.gltf';

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
                    indexAccessor: gltf.accessors[primitive.indices],
                    image: gltf.images[gltf.textures[primitiveMaterial.pbrMetallicRoughness.baseColorTexture.index].source]
                });
            }

            if (primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture) {
                primitiveUVMaps.push({
                    uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture.texCoord]],
                    indexAccessor: gltf.accessors[primitive.indices],
                    image: gltf.images[gltf.textures[primitiveMaterial.pbrMetallicRoughness.metallicRoughnessTexture.index].source]
                });
            }
        }

        if (primitiveMaterial.normalTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.normalTexture.texCoord]],
                indexAccessor: gltf.accessors[primitive.indices],
                image: gltf.images[gltf.textures[primitiveMaterial.normalTexture.index].source]
            });
        }

        if (primitiveMaterial.occlusionTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.occlusionTexture.texCoord]],
                indexAccessor: gltf.accessors[primitive.indices],
                image: gltf.images[gltf.textures[primitiveMaterial.occlusionTexture.index].source]
            });
        }

        if (primitiveMaterial.emissiveTexture) {
            primitiveUVMaps.push({
                uvAccessor: gltf.accessors[primitive.attributes["TEXCOORD_" + primitiveMaterial.emissiveTexture.texCoord]],
                indexAccessor: gltf.accessors[primitive.indices],
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
    let indexBufferView = gltf.bufferViews[map.indexAccessor.bufferView];

    let uvBufferPath = path.resolve( path.join(path.dirname(absoluteGltfPath), gltf.buffers[mapBufferView.buffer].uri) );

    let uvBuffer = fs.readFileSync(uvBufferPath);

    let indexBufferPath = path.resolve( path.join(path.dirname(absoluteGltfPath), gltf.buffers[indexBufferView.buffer].uri) );
    let indexBuffer = fs.readFileSync(indexBufferPath);

    // assume that all elements in uv maps are VEC2 : 5126 (FLOAT)
    if (map.uvAccessor.componentType != 5126 || map.uvAccessor.type != "VEC2") {
        console.log('this map is not using float values to map image textures');
        return;
    }

    let uvs = new Array();

    for (let i = 0; i < map.uvAccessor.count; i++) {
        let u = uvBuffer.readFloatLE(mapBufferView.byteOffset + 2*i*4);
        let v = uvBuffer.readFloatLE(mapBufferView.byteOffset + (2*i+1)*4);
        uvs.push([u, v]);
    }

    let indices = new Array();
    let bytePerIndex = 2;

    if (map.indexAccessor.componentType == 5121) { // UNSIGNED_BYTE
        bytePerIndex = 1;
    } else if (map.indexAccessor.componentType == 5123) { // UNSIGNED_SHORT
        bytePerIndex = 2;
    } else if (map.indexAccessor.componentType == 5125) { // UNSIGNED_INT
        bytePerIndex = 4;
    } else {
        return;
    }

    for (let i = 0; i < map.indexAccessor.count; i++) {
        
        if (bytePerIndex == 1) {
            index = indexBuffer.readUInt8(indexBufferView.byteOffset + bytePerIndex * i);
        } else if (bytePerIndex == 2) {
            index = indexBuffer.readUInt16LE(indexBufferView.byteOffset + bytePerIndex * i);
        } else {
            index = indexBuffer.readUInt32LE(indexBufferView.byteOffset + bytePerIndex * i);
        }
        indices.push(index);
    }

    let faceUvs = new Array();

    for (let i = 0; i < (indices.length/VERTEX_PER_FACE); i++) {
        faceUvs.push([uvs[indices[VERTEX_PER_FACE*i]], uvs[indices[VERTEX_PER_FACE*i+1]], uvs[indices[VERTEX_PER_FACE*i+2]]]);
    }

    output.maps.push({
        image: map.image,
        faceUvs: faceUvs
    });
});

fs.writeFileSync(path.join(path.dirname(absoluteGltfPath), 'uv_coord.json'), JSON.stringify(output, null, 2), { encoding: 'utf8' });