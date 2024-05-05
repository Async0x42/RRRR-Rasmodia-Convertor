export const applyCase = (word: string, example: string): string => {
  if (example === example.toLowerCase()) {
    return word.toLowerCase();
  } else if (example === example.toUpperCase()) {
    return word.toUpperCase();
  } else if (example[0] === example[0].toUpperCase()) {
    return word[0].toUpperCase() + word.slice(1).toLowerCase();
  }
  return word;
};
