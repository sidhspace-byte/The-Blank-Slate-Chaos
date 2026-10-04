#!/usr/bin/env node
// Parses the main <script> of index.html with a real JS parser and prints every top-level node
// (exact line ranges, names, kind) as JSON. Needs:  npm i acorn   (NODE_PATH=<dir with node_modules>)
const fs = require('fs'), acorn = require('acorn');
const html = fs.readFileSync(process.argv[2] || 'index.html', 'utf8');
const open = html.indexOf('<script>'), start = open + '<script>'.length, end = html.indexOf('</script>', start);
const lineOffset = html.slice(0, start).split('\n').length - 1;       // file line = node line + lineOffset
const js = html.slice(start, end);
const ast = acorn.parse(js, { ecmaVersion: 'latest', locations: true, allowReturnOutsideFunction: true });
const lines = js.split('\n');
const nodes = ast.body.map(n => {
  const a = n.loc.start.line + lineOffset, b = n.loc.end.line + lineOffset;
  let name = null, kind = n.type;
  if (n.type === 'FunctionDeclaration') { name = n.id.name; kind = n.async ? 'async function' : 'function'; }
  else if (n.type === 'VariableDeclaration') { name = n.declarations.map(d => (d.id && d.id.name) || '{…}').join(','); kind = n.kind; }
  else if (n.type === 'ExpressionStatement') name = lines[n.loc.start.line - 1].trim().slice(0, 70);
  return { type: n.type, kind, name, start: a, end: b };
});
console.log(JSON.stringify({ scriptStart: lineOffset + 1, scriptEnd: lineOffset + lines.length, nodes }));
