#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const argv = yargs(hideBin(process.argv))
  .option('path', {
    alias: 'p',
    description: 'Specify the path to the file or directory',
    type: 'string',
  })
  .option('debug', {
    alias: 'd',
    description: 'Enable debug logging',
    type: 'boolean',
    default: false
  })
  .help()
  .alias('help', 'h')
  .argv;

function debugLog(message) {
  if (argv.debug) {
    console.error(`[DEBUG] ${message}`);
  }
}

function processFile(filePath) {
  try {
    const code = fs.readFileSync(filePath, 'utf8');
    const records = [];
    const stack = [];
    
    // Use Babel parser with all modern features enabled
    const ast = parser.parse(code, {
      sourceType: 'module',
      plugins: [
        'importAssertions',
        'importAttributes',
        'topLevelAwait',
        'classProperties',
        'classPrivateProperties',
        'classPrivateMethods',
        'exportDefaultFrom',
        'exportNamespaceFrom',
        'dynamicImport',
      ],
    });

    // Use Babel traverse for AST walking
    traverse(ast, {
      ClassDeclaration(path) {
        const node = path.node;
        debugLog(`Found class: ${node.id.name}`);
        stack.push({ type: 'Class', name: node.id.name });
        const record = {
          type: 'Class',
          name: node.id.name,
          parameters: [],
          comments: getComments(node, code),
          code: code.substring(node.start, node.end),
          nestingLevel: stack.length - 1,
        };
        debugLog(`Adding class record: ${JSON.stringify(record)}`);
        records.push(record);

        // Process methods immediately after class declaration
        node.body.body.forEach(member => {
          if (member.type === 'ClassMethod') {
            debugLog(`Found method: ${member.key.name}, stack: ${JSON.stringify(stack)}`);
            const record = {
              type: 'Method',
              name: member.key.name,
              parentName: `Class:${node.id.name}`,
              parameters: member.params.map(param => param.name),
              comments: getComments(member, code),
              code: code.substring(member.start, member.end),
              nestingLevel: stack.length
            };
            debugLog(`Adding method record: ${JSON.stringify(record)}`);
            records.push(record);
          }
        });

        stack.pop();
      },
      
      FunctionDeclaration(path) {
        const node = path.node;
        const record = {
          type: 'Function',
          name: node.id ? node.id.name : 'anonymous',
          parameters: node.params.map(param => param.name),
          comments: getComments(node, code),
          code: code.substring(node.start, node.end),
          nestingLevel: stack.length
        };
        records.push(record);
        
        if (node.id) {
          stack.push({ type: 'Function', name: node.id.name });
        }
      },

      ImportDeclaration(path) {
        const node = path.node;
        let importInfo = {
          type: 'Import',
          source: node.source.value,
          specifiers: node.specifiers.map(spec => ({
            type: spec.type,
            name: spec.local ? spec.local.name : null,
            imported: spec.imported ? spec.imported.name : null,
          })),
          code: code.substring(node.start, node.end),
        };

        // Handle import assertions/attributes if present
        if (node.assertions && node.assertions.length > 0) {
          importInfo.assertions = node.assertions.map(assert => ({
            key: assert.key.name,
            value: assert.value.value
          }));
        }

        records.push(importInfo);
      },

      ImportExpression(path) {
        const node = path.node;
        records.push({
          type: 'Import',
          dynamic: true,
          source: node.source.type === 'StringLiteral' ? node.source.value : null,
          code: code.substring(node.start, node.end),
        });
      },

      MetaProperty(path) {
        const node = path.node;
        if (node.meta.name === 'import' && node.property.name === 'meta') {
          records.push({
            type: 'Import',
            meta_usage: true,
            code: code.substring(node.start, node.end),
          });
        }
      },

      ExportNamedDeclaration(path) {
        const node = path.node;
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

      ExportDefaultDeclaration(path) {
        const node = path.node;
        let exportValue = '';
        if (node.declaration.type === 'ArrayExpression') {
          exportValue = 'Array of configurations';
          if (node.declaration.elements) {
            exportValue = `Array of ${node.declaration.elements.length} configurations`;
          }
        } else if (node.declaration.type === 'ObjectExpression') {
          exportValue = 'Configuration object';
          if (node.declaration.properties) {
            const props = node.declaration.properties
              .map(p => p.key.name || p.key.value)
              .filter(Boolean)
              .join(', ');
            exportValue = `Configuration object with properties: ${props}`;
          }
        } else if (node.declaration.type === 'Identifier') {
          exportValue = node.declaration.name;
        }
        
        records.push({
          type: 'Export',
          isDefault: true,
          value: exportValue,
          code: code.substring(node.start, node.end),
        });
      },

      ExportAllDeclaration(path) {
        const node = path.node;
        records.push({
          type: 'Export',
          source: node.source.value,
          specifiers: [],
          code: code.substring(node.start, node.end),
        });
      },
    });

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