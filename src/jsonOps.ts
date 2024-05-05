import fs from 'fs';
import json5 from 'json5';

export const loadJsonFile = (filename: string): any => {
  const content = fs.readFileSync(filename, 'utf8');
  return json5.parse(content);
};

export const writeJsonFile = (filename: string, data: any): void => {
  fs.writeFileSync(filename, JSON.stringify(data, null, 4));
};
