#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const esprima = require('esprima');
const estraverse = require('estraverse');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

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
    const ast = esprima.parseScript(code, { 
      range: true, 
      comment: true,
      attachComment: true 
    });
    const records = [];
    const stack = [];

    estraverse.traverse(ast, {
      enter: function (node, parent) {
        if (node.type === 'ClassDeclaration') {
          stack.push({ type: 'Class', name: node.id.name });
          const record = {
            type: 'Class',
            name: node.id.name,
            parameters: [],
            comments: node.leadingComments ? node.leadingComments.map(c => c.value.trim()) : [],
            code: code.substring(node.range[0], node.range[1]),
            nestingLevel: stack.length - 1
          };
          records.push(record);
        } else if (node.type === 'MethodDefinition') {
          const className = stack[stack.length - 1].name;
          const record = {
            type: 'Function',
            name: node.key.name,
            parentName: `Class:${className}`,
            parameters: node.value.params.map(param => param.name),
            comments: (node.leadingComments || node.value.leadingComments || []).map(c => c.value.trim()),
            code: code.substring(node.range[0], node.range[1]),
            nestingLevel: stack.length
          };
          records.push(record);
        } else if (node.type.includes('Function') && !parent.type.includes('MethodDefinition')) {
          const record = {
            type: 'Function',
            name: node.id ? node.id.name : 'anonymous',
            parameters: node.params.map(param => param.name),
            comments: node.leadingComments ? node.leadingComments.map(c => c.value.trim()) : [],
            code: code.substring(node.range[0], node.range[1]),
            nestingLevel: stack.length
          };
          if (stack.length > 0) {
            const parent = stack[stack.length - 1];
            record.parentName = `${parent.type}:${parent.name}`;
          }
          records.push(record);
          
          // Push function onto stack for nested functions
          if (node.id) {
            stack.push({ type: 'Function', name: node.id.name });
          }
        }
      },
      leave: function (node) {
        if (node.type === 'ClassDeclaration' || (node.type.includes('Function') && node.id)) {
          stack.pop();
        }
      }
    });

    return records;
  } catch (error) {
    console.error(`Error processing ${filePath}: ${error.message}`);
    throw error;
  }
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