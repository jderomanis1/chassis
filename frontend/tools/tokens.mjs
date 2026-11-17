import { readFile, writeFile } from 'node:fs/promises';
const tokens = JSON.parse(await readFile(new URL('../design/tokens.json', import.meta.url)));
let css = '/* Generated from the approved tokens.json. Do not edit. */\n';
for (const [theme, value] of Object.entries(tokens.themes)) {
  css += `:root[data-theme="${theme}"]{`;
  css += Object.entries(value.color).map(([name, color]) => `--${name}:${color}`).join(';');
  css += `;--tint:${value.pillTintAlpha * 100}%}\n`;
}
await writeFile(new URL('../src/tokens.css', import.meta.url), css);
