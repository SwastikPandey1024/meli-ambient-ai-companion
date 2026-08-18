import { rollup } from 'rollup';
import ts from 'typescript';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';

function hash(content) {
  return crypto.createHash('sha256').update(content).digest('hex').slice(0, 8);
}

function resolvePackage(pkgName, subpath = '.') {
  try {
    const pkgJsonPath = path.resolve('node_modules', pkgName, 'package.json');
    if (!fs.existsSync(pkgJsonPath)) return null;

    const pkgJson = JSON.parse(fs.readFileSync(pkgJsonPath, 'utf8'));

    if (subpath === '.' || subpath === '') {
      if (pkgJson.module) {
        return path.resolve('node_modules', pkgName, pkgJson.module);
      }
      if (pkgJson.exports) {
        if (typeof pkgJson.exports === 'string') {
          return path.resolve('node_modules', pkgName, pkgJson.exports);
        }
        if (pkgJson.exports['.']) {
          const exp = pkgJson.exports['.'];
          if (typeof exp === 'string') return path.resolve('node_modules', pkgName, exp);
          if (exp.import) return path.resolve('node_modules', pkgName, exp.import);
          if (exp.default) return path.resolve('node_modules', pkgName, exp.default);
        }
      }
      if (pkgJson.main) {
        return path.resolve('node_modules', pkgName, pkgJson.main);
      }
    } else {
      if (pkgJson.exports && pkgJson.exports['./' + subpath]) {
        const exp = pkgJson.exports['./' + subpath];
        if (typeof exp === 'string') return path.resolve('node_modules', pkgName, exp);
        if (exp.import) return path.resolve('node_modules', pkgName, exp.import);
        if (exp.default) return path.resolve('node_modules', pkgName, exp.default);
      }
      const direct = path.resolve('node_modules', pkgName, subpath);
      if (fs.existsSync(direct)) return direct;
      if (fs.existsSync(direct + '.js')) return direct + '.js';
      if (fs.existsSync(direct + '.mjs')) return direct + '.mjs';
    }
  } catch {}
  return null;
}

// Custom TS/TSX + CSS Rollup plugin
function meliRollupPlugin() {
  let cssContent = '';

  return {
    name: 'meli-rollup-plugin',

    resolveId(source, importer) {
      if (source.startsWith('/')) {
        const fullPath = path.resolve(process.cwd(), source.slice(1));
        if (fs.existsSync(fullPath)) return fullPath;
        if (fs.existsSync(fullPath + '.ts')) return fullPath + '.ts';
        if (fs.existsSync(fullPath + '.tsx')) return fullPath + '.tsx';
        if (fs.existsSync(fullPath + '.js')) return fullPath + '.js';
      }

      if (source.startsWith('.')) {
        const dir = importer ? path.dirname(importer) : process.cwd();
        const resolved = path.resolve(dir, source);
        const candidates = [
          resolved,
          resolved + '.tsx',
          resolved + '.ts',
          resolved + '.jsx',
          resolved + '.js',
          resolved + '.mjs',
          resolved + '.json',
          path.join(resolved, 'index.tsx'),
          path.join(resolved, 'index.ts'),
          path.join(resolved, 'index.js'),
          path.join(resolved, 'index.mjs'),
        ];
        for (const c of candidates) {
          if (fs.existsSync(c) && fs.statSync(c).isFile()) {
            return c;
          }
        }
      }

      // Handle bare package imports
      if (!source.startsWith('.') && !source.startsWith('/') && !path.isAbsolute(source)) {
        if (source.startsWith('@tauri-apps/')) {
          return { id: source, external: false };
        }

        if (source === 'react') return path.resolve('node_modules/react/index.js');
        if (source === 'react-dom') return path.resolve('node_modules/react-dom/index.js');
        if (source === 'react-dom/client') return path.resolve('node_modules/react-dom/client.js');
        if (source === 'react/jsx-runtime') return path.resolve('node_modules/react/jsx-runtime.js');
        if (source === 'react/jsx-dev-runtime') return path.resolve('node_modules/react/jsx-dev-runtime.js');

        // Check package name parts
        const parts = source.split('/');
        let pkgName = parts[0];
        let subpath = parts.slice(1).join('/');
        if (source.startsWith('@')) {
          pkgName = parts[0] + '/' + parts[1];
          subpath = parts.slice(2).join('/');
        }

        const resolved = resolvePackage(pkgName, subpath);
        if (resolved) return resolved;
      }

      return null;
    },

    load(id) {
      if (id.startsWith('@tauri-apps/')) {
        return `
          export const getCurrentWindow = () => ({
            minimize: async () => {},
            close: async () => {},
            setDecorations: async () => {},
            setAlwaysOnTop: async () => {},
            setPosition: async () => {},
            setSize: async () => {},
          });
        `;
      }

      if (id.endsWith('.css')) {
        const code = fs.readFileSync(id, 'utf8');
        cssContent += '\n' + code;
        return 'export default "";';
      }

      if (id.endsWith('.ts') || id.endsWith('.tsx')) {
        const raw = fs.readFileSync(id, 'utf8');
        const transpiled = ts.transpileModule(raw, {
          compilerOptions: {
            module: ts.ModuleKind.ESNext,
            target: ts.ScriptTarget.ES2020,
            jsx: ts.JsxEmit.ReactJSX,
            esModuleInterop: true,
            allowSyntheticDefaultImports: true,
          },
          fileName: id,
        });
        return {
          code: transpiled.outputText,
          map: transpiled.sourceMapText,
        };
      }

      if (id.endsWith('.json')) {
        const raw = fs.readFileSync(id, 'utf8');
        return `export default ${raw};`;
      }

      return null;
    },

    generateBundle() {
      if (cssContent.trim()) {
        const cssHash = hash(cssContent);
        this.emitFile({
          type: 'asset',
          fileName: `assets/index-${cssHash}.css`,
          source: cssContent,
        });
      }
    },
  };
}

// React 18 ESM adapter
function reactEsmPlugin() {
  return {
    name: 'react-esm-plugin',
    transform(code, id) {
      if (id.endsWith('react\\index.js') || id.endsWith('react/index.js')) {
        return `
          import * as ReactAll from './cjs/react.production.min.js';
          const React = ReactAll.default || ReactAll;
          export default React;
          export const useState = React.useState;
          export const useEffect = React.useEffect;
          export const useMemo = React.useMemo;
          export const useCallback = React.useCallback;
          export const useRef = React.useRef;
          export const useContext = React.useContext;
          export const createContext = React.createContext;
          export const createElement = React.createElement;
          export const cloneElement = React.cloneElement;
          export const isValidElement = React.isValidElement;
          export const Fragment = React.Fragment;
          export const StrictMode = React.StrictMode;
          export const Children = React.Children;
          export const forwardRef = React.forwardRef;
          export const memo = React.memo;
          export const lazy = React.lazy;
          export const Suspense = React.Suspense;
          export const useId = React.useId;
          export const useDeferredValue = React.useDeferredValue;
          export const useTransition = React.useTransition;
          export const useImperativeHandle = React.useImperativeHandle;
          export const useLayoutEffect = React.useLayoutEffect;
          export const useDebugValue = React.useDebugValue;
          export const useSyncExternalStore = React.useSyncExternalStore;
          export const useInsertionEffect = React.useInsertionEffect;
          export const version = React.version;
          export const Component = React.Component;
          export const PureComponent = React.PureComponent;
        `;
      }

      if (id.endsWith('react-dom\\client.js') || id.endsWith('react-dom/client.js')) {
        return `
          import ReactDOM from 'react-dom';
          export const createRoot = ReactDOM.createRoot;
          export const hydrateRoot = ReactDOM.hydrateRoot;
          export default { createRoot, hydrateRoot };
        `;
      }

      if (id.endsWith('react-dom\\index.js') || id.endsWith('react-dom/index.js')) {
        return `
          import * as ReactDOMAll from './cjs/react-dom.production.min.js';
          const ReactDOM = ReactDOMAll.default || ReactDOMAll;
          export default ReactDOM;
          export const createPortal = ReactDOM.createPortal;
          export const flushSync = ReactDOM.flushSync;
          export const findDOMNode = ReactDOM.findDOMNode;
          export const unmountComponentAtNode = ReactDOM.unmountComponentAtNode;
          export const version = ReactDOM.version;
          export const createRoot = ReactDOM.createRoot;
          export const hydrateRoot = ReactDOM.hydrateRoot;
        `;
      }

      if (id.endsWith('react\\jsx-runtime.js') || id.endsWith('react/jsx-runtime.js')) {
        return `
          import * as JsxRuntime from './cjs/react-jsx-runtime.production.min.js';
          const jsxPkg = JsxRuntime.default || JsxRuntime;
          export const jsx = jsxPkg.jsx;
          export const jsxs = jsxPkg.jsxs;
          export const Fragment = jsxPkg.Fragment;
          export default jsxPkg;
        `;
      }

      if (id.endsWith('react\\jsx-dev-runtime.js') || id.endsWith('react/jsx-dev-runtime.js')) {
        return `
          import * as JsxRuntime from './cjs/react-jsx-runtime.production.min.js';
          const jsxPkg = JsxRuntime.default || JsxRuntime;
          export const jsxDEV = jsxPkg.jsx;
          export const jsx = jsxPkg.jsx;
          export const jsxs = jsxPkg.jsxs;
          export const Fragment = jsxPkg.Fragment;
          export default jsxPkg;
        `;
      }

      if (id.includes('cjs\\react.production.min.js') || id.includes('cjs/react.production.min.js') ||
          id.includes('cjs\\react-dom.production.min.js') || id.includes('cjs/react-dom.production.min.js') ||
          id.includes('cjs\\react-jsx-runtime.production.min.js') || id.includes('cjs/react-jsx-runtime.production.min.js') ||
          id.includes('scheduler\\cjs') || id.includes('scheduler/cjs')) {
        return `
          var exports = {};
          var module = { exports: exports };
          var process = { env: { NODE_ENV: 'production' } };
          (function() {
            ${code}
          })();
          export default module.exports;
        `;
      }

      if (id.endsWith('scheduler\\index.js') || id.endsWith('scheduler/index.js')) {
        return `
          import * as SchedulerAll from './cjs/scheduler.production.min.js';
          export default SchedulerAll.default || SchedulerAll;
        `;
      }

      return null;
    }
  };
}

export async function buildApp() {
  console.log('🚀 Building Meli Ambient Companion frontend...');

  // Clean dist directory
  if (fs.existsSync('dist')) {
    fs.rmSync('dist', { recursive: true, force: true });
  }
  fs.mkdirSync('dist/assets', { recursive: true });

  // Copy public assets to dist
  if (fs.existsSync('public')) {
    fs.cpSync('public', 'dist', { recursive: true });
    console.log('✓ Copied public assets to dist/');
  }

  const bundle = await rollup({
    input: path.resolve('src/main.tsx'),
    plugins: [
      reactEsmPlugin(),
      meliRollupPlugin(),
    ],
  });

  const { output } = await bundle.generate({
    format: 'es',
    entryFileNames: 'assets/index-[hash].js',
    chunkFileNames: 'assets/[name]-[hash].js',
    assetFileNames: 'assets/[name]-[hash][extname]',
  });

  let jsBundleName = '';
  let cssBundleName = '';

  for (const chunk of output) {
    const destPath = path.join('dist', chunk.fileName);
    fs.mkdirSync(path.dirname(destPath), { recursive: true });

    if (chunk.type === 'chunk') {
      fs.writeFileSync(destPath, chunk.code, 'utf8');
      if (chunk.isEntry) jsBundleName = chunk.fileName;
    } else {
      fs.writeFileSync(destPath, chunk.source);
      if (chunk.fileName.endsWith('.css')) cssBundleName = chunk.fileName;
    }
  }

  // Generate dist/index.html with hashed assets
  const htmlTemplate = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="/states/meli_idle.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Meli — Ambient AI Companion</title>
    ${cssBundleName ? `<link rel="stylesheet" crossorigin href="/${cssBundleName}">` : ''}
  </head>
  <body>
    <div id="root"></div>
    <script type="module" crossorigin src="/${jsBundleName}"></script>
  </body>
</html>`;

  fs.writeFileSync('dist/index.html', htmlTemplate, 'utf8');
  console.log(`✓ Generated dist/index.html (JS: /${jsBundleName}, CSS: /${cssBundleName})`);
  console.log('✨ Build finished successfully!');
}

if (process.argv[1]?.endsWith('bundle.mjs') || process.argv[1]?.endsWith('build.mjs')) {
  buildApp().catch(err => {
    console.error('Build failed:', err);
    process.exit(1);
  });
}
