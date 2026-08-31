import fs from "node:fs";
import path from "node:path";

function _mkdir(_path: string) {
  if (!fs.existsSync(_path)) {
    fs.mkdirSync(_path, { recursive: true });
  }
  return _path;
}

export const rootDir = path.resolve(process.env.APP_ROOT_DIR || import.meta.dirname);
export const tempDir = _mkdir(path.join(rootDir, "tmp"));
