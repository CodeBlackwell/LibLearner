#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const acorn = require('acorn');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');
const walk = require('acorn-walk');

const argv = yargs(hideBin(process.argv))
  .option('path', {
    alias: 'p',
    description: 'Specify the path to the file or directory',
    type: 'string',
  })
  .help()
  .alias('help', 'h')
  .argv;

function processFile(filePath) {
  try {
    const code = fs.readFileSync(filePath, 'utf8');
    const ast = acorn.parse(code, {
      sourceType: 'module',
      ecmaVersion: 'latest',
      locations: true,
      ranges: true,
    });

    const records = [];
    const stack = [];

    walk.simple(ast, {
      ImportDeclaration(node) {
        records.push({
          type: 'Import',
          source: node.source.value,
          specifiers: node.specifiers.map(spec => ({
            type: spec.type,
            name: spec.local ? spec.local.name : null,
            imported: spec.imported ? spec.imported.name : null,
          })),
          code: code.substring(node.start, node.end),
        });
      },
      ImportExpression(node) {
        records.push({
          type: 'Import',
          dynamic: true,
          source: node.source.type === 'Literal' ? node.source.value : null,
          code: code.substring(node.start, node.end),
        });
      },
      MetaProperty(node) {
        if (node.meta.name === 'import' && node.property.name === 'meta') {
          records.push({
            type: 'Import',
            meta_usage: true,
            code: code.substring(node.start, node.end),
          });
        }
      },
      ExportNamedDeclaration(node) {
        records.push({
          type: 'Export',
          source: node.source ? node.source.value : null,
          specifiers: node.specifiers ? node.specifiers.map(spec => ({
            type: spec.type,
            name: spec.local ? spec.local.name : null,
            exported: spec.exported ? spec.exported.name : null,
          })) : [],
          code: code.substring(node.start, node.end),
        });
      },
      ExportAllDeclaration(node) {
        records.push({
          type: 'Export',
          source: node.source.value,
          specifiers: [],
          code: code.substring(node.start, node.end),
        });
      },
      ClassDeclaration(node) {
        stack.push({ type: 'Class', name: node.id.name });
        const record = {
          type: 'Class',
          name: node.id.name,
          parameters: [],
          comments: getComments(node, code),
          code: code.substring(node.start, node.end),
          nestingLevel: stack.length - 1,
        };
        records.push(record);
      },
      MethodDefinition(node) {
        if (stack.length > 0) {
          const className = stack[stack.length - 1].name;
          const record = {
            type: 'Function',
            name: node.key.name,
            parentName: `Class:${className}`,
            parameters: node.value.params.map(param => param.name),
            comments: getComments(node, code),
            code: code.substring(node.start, node.end),
            nestingLevel: stack.length,
          };
          records.push(record);
        }
      },
      FunctionDeclaration(node) {
        const record = {
          type: 'Function',
          name: node.id ? node.id.name : 'anonymous',
          parameters: node.params.map(param => param.name),
          comments: getComments(node, code),
          code: code.substring(node.start, node.end),
          nestingLevel: stack.length,
        };
        if (stack.length > 0) {
          const parent = stack[stack.length - 1];
          record.parentName = `${parent.type}:${parent.name}`;
        }
        records.push(record);

        if (node.id) {
          stack.push({ type: 'Function', name: node.id.name });
        }
      },
      'ClassDeclaration:exit'(node) {
        stack.pop();
      },
      'FunctionDeclaration:exit'(node) {
        if (node.id) {
          stack.pop();
        }
      },
    });

    // Handle stack cleanup after traversal
    stack.length = 0;

    return records;
  } catch (error) {
    console.error(`Error processing ${filePath}: ${error.message}`);
    throw error;
  }
}

function getComments(node, code) {
  const comments = [];
  if (node.leadingComments) {
    node.leadingComments.forEach(comment => {
      comments.push(code.substring(comment.start, comment.end).trim());
    });
  }
  return comments;
}

// Process the file and output JSON to stdout
const filePath = argv.path;
if (!filePath) {
  console.error('No file path provided');
  process.exit(1);
}

try {
  const results = processFile(filePath);
  console.log(JSON.stringify(results));
} catch (error) {
  process.exit(1);
}