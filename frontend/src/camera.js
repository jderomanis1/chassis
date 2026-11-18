export function camerasClose(before, after, pixels = 1) {
  const read = (value) => {
    const translate = /translate(?:3d)?\(\s*(-?\d+(?:\.\d+)?)px,\s*(-?\d+(?:\.\d+)?)px/i.exec(String(value || ''));
    const scale = /scale\(\s*(-?\d+(?:\.\d+)?)/i.exec(String(value || ''));
    if (!translate) return null;
    return { x: Number(translate[1]), y: Number(translate[2]), zoom: scale ? Number(scale[1]) : 1 };
  };
  const left = read(before);
  const right = read(after);
  if (!left || !right) return false;
  return Math.abs(left.x - right.x) <= pixels
    && Math.abs(left.y - right.y) <= pixels
    && Math.abs(left.zoom - right.zoom) <= 0.01;
}
