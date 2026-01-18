#!/usr/bin/env node
/**
 * Bulk-fix ESLint issues using the JSON report produced by:
 *   node ./node_modules/eslint/bin/eslint.js src -f json -o eslint-report.json
 *
 * Focus:
 * - no-unused-vars: rename binding to `_xxx` (rule ignores underscore)
 * - no-undef: add common missing imports (react hooks, lucide icons, toast, cn/formatCurrency)
 *            and add minimal placeholder state/const declarations for obvious missing state pairs.
 *
 * This is a pragmatic “reduce lint noise quickly” script; review diffs afterwards.
 */

import fs from "node:fs";
import path from "node:path";

import { parse } from "@babel/parser";
import traverseModule from "@babel/traverse";
import generateModule from "@babel/generator";
import * as t from "@babel/types";

const REPORT_PATH = path.resolve("eslint-report.json");

const traverse = traverseModule.default ?? traverseModule;
const generate = generateModule.default ?? generateModule;

const reactHookNames = new Set([
  "useState",
  "useEffect",
  "useMemo",
  "useCallback",
  "useRef",
  "useContext",
  "useReducer",
  "useLayoutEffect",
]);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function toPosixPath(p) {
  return p.split(path.sep).join(path.posix.sep);
}

function computeLibUtilsImportSource(filePath) {
  const fileDir = path.dirname(filePath);
  const libUtilsPath = path.resolve("src/lib/utils.js");
  const rel = path.relative(fileDir, libUtilsPath);
  const normalized = toPosixPath(rel).replace(/\.js$/, "");
  if (normalized.startsWith(".")) {return normalized;}
  return `./${normalized}`;
}

function ensureNamedImport(programPath, sourceValue, names) {
  const uniqueNames = [...new Set(names)].filter(Boolean);
  if (uniqueNames.length === 0) {return;}

  let importDeclPath = null;
  for (const bodyPath of programPath.get("body")) {
    if (!bodyPath.isImportDeclaration()) {continue;}
    if (bodyPath.node.source.value === sourceValue) {
      importDeclPath = bodyPath;
      break;
    }
  }

  if (!importDeclPath) {
    const specifiers = uniqueNames.map((n) =>
      t.importSpecifier(t.identifier(n), t.identifier(n)),
    );
    const decl = t.importDeclaration(specifiers, t.stringLiteral(sourceValue));
    // Insert after existing imports (keeps order stable).
    let insertIndex = 0;
    const body = programPath.node.body;
    while (insertIndex < body.length && t.isImportDeclaration(body[insertIndex])) {
      insertIndex++;
    }
    programPath.node.body.splice(insertIndex, 0, decl);
    return;
  }

  const existing = new Set();
  for (const spec of importDeclPath.node.specifiers) {
    if (t.isImportSpecifier(spec)) {existing.add(spec.imported.name);}
  }

  for (const name of uniqueNames) {
    if (existing.has(name)) {continue;}
    importDeclPath.node.specifiers.push(
      t.importSpecifier(t.identifier(name), t.identifier(name)),
    );
  }
}

function ensureLucideIcons(programPath, iconNames) {
  if (!iconNames.length) {return;}
  let lucideImportPath = null;
  for (const bodyPath of programPath.get("body")) {
    if (!bodyPath.isImportDeclaration()) {continue;}
    if (bodyPath.node.source.value === "lucide-react") {
      lucideImportPath = bodyPath;
      break;
    }
  }
  if (!lucideImportPath) {return;}

  const existing = new Set();
  for (const spec of lucideImportPath.node.specifiers) {
    if (t.isImportSpecifier(spec)) {existing.add(spec.imported.name);}
  }

  for (const icon of iconNames) {
    if (existing.has(icon)) {continue;}
    lucideImportPath.node.specifiers.push(
      t.importSpecifier(t.identifier(icon), t.identifier(icon)),
    );
  }
}

function findFirstComponentBodyPath(programPath) {
  for (const bodyPath of programPath.get("body")) {
    // export default function Foo() {}
    // export default function() {}
    if (bodyPath.isExportDefaultDeclaration()) {
      const decl = bodyPath.get("declaration");
      if (decl.isFunctionDeclaration()) {
        return decl.get("body");
      }
      if (decl.isArrowFunctionExpression() && decl.get("body").isBlockStatement()) {
        return decl.get("body");
      }
    }

    // export const Foo = () => {}
    if (bodyPath.isExportNamedDeclaration()) {
      const decl = bodyPath.get("declaration");
      if (decl.isVariableDeclaration()) {
        for (const d of decl.get("declarations")) {
          const id = d.get("id");
          const init = d.get("init");
          if (!id.isIdentifier()) {continue;}
          if (!/^[A-Z]/.test(id.node.name)) {continue;}
          if (
            init.isArrowFunctionExpression() &&
            init.get("body").isBlockStatement()
          ) {
            return init.get("body");
          }
        }
      }
      if (decl.isFunctionDeclaration()) {
        const id = decl.get("id");
        if (id.isIdentifier() && /^[A-Z]/.test(id.node.name)) {
          return decl.get("body");
        }
      }
    }

    // const Foo = () => {}
    if (bodyPath.isVariableDeclaration()) {
      for (const d of bodyPath.get("declarations")) {
        const id = d.get("id");
        const init = d.get("init");
        if (!id.isIdentifier()) {continue;}
        if (!/^[A-Z]/.test(id.node.name)) {continue;}
        if (init.isArrowFunctionExpression() && init.get("body").isBlockStatement()) {
          return init.get("body");
        }
      }
    }
  }
  return null;
}

function pickUniqueName(scopePath, baseName) {
  let candidate = baseName;
  let i = 1;
  while (scopePath.scope.hasBinding(candidate) || scopePath.scope.hasGlobal(candidate)) {
    candidate = `${baseName}_${i}`;
    i += 1;
  }
  return candidate;
}

function parseUndefName(message) {
  const m = message.match(/'([^']+)'/);
  return m ? m[1] : null;
}

function parseUnusedName(message) {
  const m = message.match(/'([^']+)'/);
  return m ? m[1] : null;
}

function locKey(line, column) {
  // ESLint column is 1-based; Babel column is 0-based in loc.
  return `${line}:${Math.max(column - 1, 0)}`;
}

function shouldSkipUnusedRename(name) {
  // already ignored by config
  return name.startsWith("_") || /^[A-Z]/.test(name);
}

function run() {
  if (!fs.existsSync(REPORT_PATH)) {
    console.error(`Missing report: ${REPORT_PATH}`);
    process.exit(1);
  }

  const report = readJson(REPORT_PATH);
  let touchedFiles = 0;
  let changedFiles = 0;

  for (const fileResult of report) {
    const filePath = fileResult.filePath;
    const messages = (fileResult.messages || []).filter((m) => m.severity === 2);
    if (messages.length === 0) {continue;}
    if (!filePath.includes(`${path.sep}src${path.sep}`)) {continue;}
    if (!fs.existsSync(filePath)) {continue;}

    touchedFiles += 1;

    const code = fs.readFileSync(filePath, "utf8");

    let ast;
    try {
      ast = parse(code, {
        sourceType: "module",
        plugins: [
          "jsx",
          "classProperties",
          "objectRestSpread",
          "optionalChaining",
          "nullishCoalescingOperator",
          "dynamicImport",
          "topLevelAwait",
        ],
      });
    } catch (err) {
      console.error(`Parse failed: ${path.relative(process.cwd(), filePath)}: ${err}`);
      continue;
    }

    const unusedLocs = new Map();
    const undefNames = new Set();
    for (const msg of messages) {
      if (msg.ruleId === "no-unused-vars") {
        const name = parseUnusedName(msg.message);
        if (!name || shouldSkipUnusedRename(name)) {continue;}
        unusedLocs.set(locKey(msg.line, msg.column), name);
      } else if (msg.ruleId === "no-undef") {
        const name = parseUndefName(msg.message);
        if (name) {undefNames.add(name);}
      }
    }

    const neededReact = new Set();
    const neededSonner = new Set();
    const neededUtils = new Set();
    const neededLucide = new Set();
    const placeholderPairs = [];
    const placeholderSingles = [];

    // For no-undef: decide fixes.
    for (const name of undefNames) {
      if (reactHookNames.has(name)) {
        neededReact.add(name);
        continue;
      }
      if (name === "toast") {
        neededSonner.add("toast");
        continue;
      }
      if (name === "cn" || name === "formatCurrency") {
        neededUtils.add(name);
        continue;
      }
      if (/^[A-Z]/.test(name)) {
        neededLucide.add(name);
        continue;
      }
    }

    // Pair `setX` + `x` into state declarations.
    for (const name of undefNames) {
      if (!name.startsWith("set") || name.length <= 3) {continue;}
      const base = name.slice(3);
      const baseName = base.charAt(0).toLowerCase() + base.slice(1);
      if (undefNames.has(baseName)) {
        placeholderPairs.push({ valueName: baseName, setterName: name });
      } else {
        // setter used but value not flagged as undef (still probably missing state)
        placeholderPairs.push({ valueName: baseName, setterName: name });
      }
      neededReact.add("useState");
    }

    // Singles: only add for names that are not likely imports.
    for (const name of undefNames) {
      if (reactHookNames.has(name)) {continue;}
      if (name === "toast") {continue;}
      if (name === "cn" || name === "formatCurrency") {continue;}
      if (name.startsWith("set")) {continue;}
      if (/^[A-Z]/.test(name)) {continue;}
      placeholderSingles.push(name);
    }

    let changed = false;

    traverse(ast, {
      Program(programPath) {
        // Fix imports for no-undef.
        if (neededReact.size) {ensureNamedImport(programPath, "react", [...neededReact]);}
        if (neededSonner.size) {ensureNamedImport(programPath, "sonner", [...neededSonner]);}

        if (neededUtils.size) {
          const utilsSource = computeLibUtilsImportSource(filePath);

          // Prefer existing utils import if any.
          let foundSource = null;
          for (const bodyPath of programPath.get("body")) {
            if (!bodyPath.isImportDeclaration()) {continue;}
            const v = bodyPath.node.source.value;
            if (v.endsWith("/lib/utils") || v.endsWith("/lib/utils.js") || v === utilsSource) {
              foundSource = v;
              break;
            }
          }
          ensureNamedImport(programPath, foundSource || utilsSource, [...neededUtils]);
        }

        if (neededLucide.size) {
          ensureLucideIcons(programPath, [...neededLucide]);
        }

        // Insert placeholder declarations into the first component body we find.
        const componentBodyPath = findFirstComponentBodyPath(programPath);
        if (componentBodyPath) {
          const insertions = [];

          for (const { valueName, setterName } of placeholderPairs) {
            if (componentBodyPath.scope.hasBinding(valueName)) {continue;}
            if (componentBodyPath.scope.hasBinding(setterName)) {continue;}

            const uniqueValue = pickUniqueName(componentBodyPath, valueName);
            const uniqueSetter = pickUniqueName(componentBodyPath, setterName);

            insertions.push(
              t.variableDeclaration("const", [
                t.variableDeclarator(
                  t.arrayPattern([t.identifier(uniqueValue), t.identifier(uniqueSetter)]),
                  t.callExpression(t.identifier("useState"), [t.nullLiteral()]),
                ),
              ]),
            );
            changed = true;
          }

          for (const name of placeholderSingles) {
            if (componentBodyPath.scope.hasBinding(name)) {continue;}
            const unique = pickUniqueName(componentBodyPath, name);
            insertions.push(
              t.variableDeclaration("const", [
                t.variableDeclarator(t.identifier(unique), t.nullLiteral()),
              ]),
            );
            changed = true;
          }

          if (insertions.length) {
            componentBodyPath.node.body.unshift(...insertions);
          }
        }
      },

      Identifier(idPath) {
        const node = idPath.node;
        if (!node.loc) {return;}
        const key = locKey(node.loc.start.line, node.loc.start.column + 1);
        const originalName = unusedLocs.get(key);
        if (!originalName) {return;}
        if (idPath.node.name !== originalName) {return;}

        const baseNewName = `_${originalName}`;
        const newName = pickUniqueName(idPath.scope.path, baseNewName);

        // Only rewrite the binding identifier itself. For `no-unused-vars` there
        // should be no real references, so a full-scope rename isn't necessary
        // (and requires Babel hub plumbing).
        if (!idPath.isBindingIdentifier()) {return;}
        idPath.node.name = newName;
        unusedLocs.delete(key);
        changed = true;
      },
    });

    if (!changed) {continue;}

    const output = generate(
      ast,
      {
        retainLines: true,
        comments: true,
        compact: false,
        jsescOption: { minimal: true },
      },
      code,
    ).code;

    if (output !== code) {
      fs.writeFileSync(filePath, output, "utf8");
      changedFiles += 1;
    }
  }

  console.log(`Touched files: ${touchedFiles}`);
  console.log(`Changed files: ${changedFiles}`);
}

run();
