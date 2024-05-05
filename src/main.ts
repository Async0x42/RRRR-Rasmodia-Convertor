import path from 'path';
import { loadJsonFile, writeJsonFile } from './jsonOps';
import { loadReplacements } from './fileOps';
import { replacementSwap } from './replacementSwap';
import { DATA_FOLDER_PATH } from './config';

const main = async () => {
  try {
    const replacementMap = loadReplacements();
    const json_data = loadJsonFile(path.join(DATA_FOLDER_PATH, 'default.json'));
    const output_data: { [key: string]: string } = {};

    for (const key in json_data) {
      const swapped_text = replacementSwap(json_data[key], replacementMap);
      if (swapped_text !== json_data[key]) {
        output_data[key] = swapped_text;
        console.log(`Difference found for '${key}': ${swapped_text}`);
      }
    }

    if (Object.keys(output_data).length > 0) {
      writeJsonFile(path.join(DATA_FOLDER_PATH, 'output.json'), output_data);
    }
  } catch (e) {
    console.error(e);
  }
};

main();
