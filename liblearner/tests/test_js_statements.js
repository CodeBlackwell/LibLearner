// Test JavaScript file for JS Processor

export * from "d3-array";
import assert from "assert";
import {readdir, readFile, stat} from "fs/promises";
import {fileURLToPath, dirname, resolve} from "url";
import {readFileSync} from "fs";
import d3 from "d3";

// Additional content to ensure the file is valid
console.log("Test file for JS Processor");

// Test dynamic imports and import.meta
async function testDynamicImports() {
  const packagePath = resolve(dirname(fileURLToPath(import.meta.url)), "../package.json");
  const packageData = JSON.parse(readFileSync(packagePath));

  for (const moduleName in packageData.dependencies) {
    it(`d3 exports everything from ${moduleName}`, async () => {
      const module = await import(moduleName);
      for (const propertyName in module) {
        if (propertyName !== "version") {
          assert(propertyName in d3, `${moduleName} exports ${propertyName}`);
        }
      }
    });
  }
}

testDynamicImports();
