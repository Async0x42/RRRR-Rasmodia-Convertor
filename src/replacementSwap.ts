import { applyCase } from './applyCase';

export const replacementSwap = (
  text: string,
  replacementMap: Record<string, string>
): string => {
  const regex = new RegExp(
    `\\b(${Object.keys(replacementMap).join('|')})\\b`,
    'gi'
  );
  return text.replace(regex, (match) => {
    const matchedKey = Object.keys(replacementMap).find((key) =>
      new RegExp(key, 'i').test(match)
    );
    if (matchedKey) {
      return applyCase(replacementMap[matchedKey], match);
    }
    return match;
  });
};
