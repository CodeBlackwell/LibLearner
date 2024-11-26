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
    const ast = esprima.parseScript(code, { range: true, comment: true });
    let orderCounter = 0;
    const records = [];
    const stack = [];
    const nestKeyStack = [];

    estraverse.traverse(ast, {
      enter: function (node, parent) {
        if (node.type.includes('Function') || node.type === 'ClassDeclaration' || node.type === 'MethodDefinition' || (node.type === 'VariableDeclaration' && node.kind === 'const') || node.type === 'IfStatement') {
          orderCounter++;
          const [start, end] = node.range;
          const codeSnippet = code.substring(start, end);
          let elementType = '';
          let elementName = '';
          let parameters = [];
          let comments = [];

          if (node.type === 'MethodDefinition') {
            elementType = 'Function';
            elementName = node.key.name;
            parameters = node.value.params.map(param => param.name);
          } else if (node.type.includes('Function')) {
            elementType = 'Function';
            elementName = node.id ? node.id.name : parent && parent.type === 'VariableDeclarator' ? parent.id.name : `Anonymous${stack.length > 0 ? '.' + stack.map(e => e.name).join('.') : ''}`;
            parameters = node.params.map(param => param.name);
          } else if (node.type === 'ClassDeclaration') {
            elementType = 'Class';
            elementName = node.id.name;
          } else if (node.type === 'IfStatement') {
            elementType = 'Conditional';
            elementName = 'if';
          } else {
            elementType = 'Constant';
            elementName = node.declarations[0].id.name;
          }

          if (node.leadingComments) {
            comments = node.leadingComments.map(comment => comment.value.trim());
          }

          const nestingLevel = stack.length;
          const parentName = stack.map(e => `${e.type}:${e.name}`).join(' -> ');
          const nestKey = nestKeyStack.join('-');

          records.push({
            order: orderCounter,
            type: elementType,
            name: elementName,
            code: codeSnippet,
            nestingLevel,
            parentName,
            parameters,
            nestKey,
            filePath,
            comments
          });

          stack.push({ type: elementType, name: elementName });
          nestKeyStack.push(orderCounter);
        }
      },
      leave: function (node) {
        if (node.type.includes('Function') || node.type === 'ClassDeclaration' || node.type === 'MethodDefinition' || (node.type === 'VariableDeclaration' && node.kind === 'const') || node.type === 'IfStatement') {
          stack.pop();
          nestKeyStack.pop();
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