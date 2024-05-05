// src/fileOps.ts
import fs from 'fs';
import { parse } from 'csv-parse/sync';
import { REPLACEMENTS_FILE_PATH } from './config';

export const loadReplacements = (): Record<string, string> => {
  const content = fs.readFileSync(REPLACEMENTS_FILE_PATH, {
    encoding: 'utf-8',
  });
  const records = parse(content, {
    delimiter: '|',
    columns: true,
  });
  return records.reduce((acc: Record<string, string>, row: any) => {
    acc[row[0]] = row[1];
    return acc;
  }, {});
};
