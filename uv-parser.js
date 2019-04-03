const argv = require('yargs').argv;
const fs = require('fs');

let input = argv.input;

if (!input || !fs.existsSync(input)) {
    console.log('input file not found');
    process.exit(1);
}