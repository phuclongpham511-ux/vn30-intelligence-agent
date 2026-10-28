// Creates a NEW offline frontend snapshot. Never launches/stops services or builds in the source checkout.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {acceptanceDataset} from '../frontend/tests/fixtures/acceptance-replay.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),frontend=path.join(root,'frontend');
const [destination,evidenceDir]=process.argv.slice(2);
if(!destination||!evidenceDir)throw Error('Usage: node scripts/prepare_product_acceptance.mjs NEW_SNAPSHOT SAVED_FINANCIAL_EVIDENCE_DIRECTORY');
const output=path.resolve(destination);
if(fs.existsSync(output)||output.startsWith(root+path.sep)||!fs.existsSync(path.dirname(output)))throw Error('Use a new external artifact directory with an existing parent. No existing directory is changed.');
const hash=file=>createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const saved={FPT:{}};
for(const frequency of ['annual','quarterly','ttm']) {
 const filename=path.resolve(evidenceDir,`FPT-${frequency}-saved-replay.json`);
 const data=JSON.parse(fs.readFileSync(filename,'utf8'));
 if(data.ticker!=='FPT'||data.period_type!==frequency||data.is_fixture!==false||data.fundamental_summary?.metrics.some(row=>row.status==='QUALIFIED'))throw Error('Expected existing unqualified FPT saved display evidence; do not relabel another packet.');
 saved.FPT[frequency]=data;
}
fs.mkdirSync(output);
for(const name of ['app','lib','public'])fs.cpSync(path.join(frontend,name),path.join(output,name),{recursive:true});
for(const name of ['package.json','package-lock.json','tsconfig.json','next-env.d.ts','postcss.config.mjs','AGENTS.md'])fs.copyFileSync(path.join(frontend,name),path.join(output,name));
fs.mkdirSync(path.join(output,'tests','fixtures'),{recursive:true});
for(const name of ['acceptance-replay.mjs','fundamental-summary.mjs','stock-intelligence.mjs'])fs.copyFileSync(path.join(frontend,'tests','fixtures',name),path.join(output,'tests','fixtures',name));
fs.symlinkSync(path.join(frontend,'node_modules'),path.join(output,'node_modules'),'junction');
const dataset=acceptanceDataset(saved);
fs.writeFileSync(path.join(output,'replay-data.json'),JSON.stringify(dataset,null,2));
const edits=[];
function patch(relative,before,after){const target=path.join(output,relative),text=fs.readFileSync(target,'utf8');if(!text.includes(before)||text.split(before).length!==2)throw Error('Snapshot patch target changed: '+relative);fs.writeFileSync(target,text.replace(before,after));edits.push(relative);}
patch('lib/watchlist.ts','"vn30.watchlist.v1"','"woofi.acceptance.watchlist.v1"');
patch('lib/universe.ts',"'vn30.recent-equity-searches.v1'","'woofi.acceptance.recent-searches.v1'");
patch('lib/translations.ts','"woofi.language.v1"','"woofi.acceptance.language.v1"');
patch('app/components/app-shell/AppShell.tsx','<ThemeProvider attribute="class"','<ThemeProvider storageKey="woofi.acceptance.theme.v1" attribute="class"');
patch('app/components/app-shell/AppShell.tsx','SIMULATED UI VALIDATION — NOT LIVE SSI','OFFLINE ACCEPTANCE REPLAY · FIXED 18 OCT 2026 12:00 ICT · DEMO + SAVED UNQUALIFIED EVIDENCE · ISOLATED WATCHLIST');
const apiWrapper=`import {replayHandler} from '@/tests/fixtures/acceptance-replay.mjs';\nimport data from '@/replay-data.json';\nexport const dynamic='force-dynamic';\nexport const runtime='nodejs';\nexport const GET=replayHandler(data);\nexport const POST=GET;\n`;
const sourceHashes={};
function walk(directory,fn){for(const file of fs.readdirSync(directory,{withFileTypes:true})){const target=path.join(directory,file.name);if(file.isDirectory())walk(target,fn);else if(file.isFile())fn(target);}}
for(const dir of ['app','lib'])walk(path.join(frontend,dir),file=>{sourceHashes[path.relative(frontend,file).replaceAll('\\','/')]=hash(file);});
walk(path.join(output,'app','api'),file=>{if(path.basename(file)==='route.ts'){fs.writeFileSync(file,apiWrapper);edits.push(path.relative(output,file));}});
fs.mkdirSync(path.join(output,'app','api','acceptance'));fs.writeFileSync(path.join(output,'app','api','acceptance','route.ts'),apiWrapper);
fs.mkdirSync(path.join(output,'app','demo','acceptance'),{recursive:true});
fs.writeFileSync(path.join(output,'app','demo','acceptance','page.tsx'),`import Link from 'next/link';\nexport default function Page(){return <section className="panel p-5 space-y-4"><h1>Product acceptance · OFFLINE REPLAY</h1><p>Fixed observation clock: 18 October 2026 12:00 ICT. Synthetic identities/news/discussions/actions and ABC financials are DEMO. FPT financials replay saved evidence with unknown reporting basis; no live qualification.</p><p>Watchlist, recent searches, language and theme use dedicated acceptance storage keys. Original browser Watchlist is neither read nor changed. Do not follow source fixture links as original publications.</p><nav className="flex flex-wrap gap-4"><Link href="/stocks/AAA">AAA · News + Community</Link><Link href="/stocks/ABC#stock-fundamentals">ABC · DEMO financials</Link><Link href="/stocks/ABC#stock-actions">ABC · DEMO action states</Link><Link href="/stocks/FPT#stock-fundamentals">FPT · saved unqualified financials</Link><Link href="/stocks/BBB">BBB · cross-ticker</Link><Link href="/watchlist">Watchlist · isolated review state</Link><Link href="/demo/market">Heatmap copy check</Link></nav></section>;}\n`);
// Unknown API calls stay local and fail closed; never fall back to production.
const pkg=JSON.parse(fs.readFileSync(path.join(output,'package.json'),'utf8'));
pkg.scripts.start='next start --hostname 127.0.0.1';fs.writeFileSync(path.join(output,'package.json'),JSON.stringify(pkg,null,2));
fs.writeFileSync(path.join(output,'.env.local'),'NEXT_PUBLIC_WOOFI_VALIDATION=replay\nNEXT_TELEMETRY_DISABLED=1\nBACKEND_URL=http://127.0.0.1:1\n');
const manifest={kind:'OFFLINE_REPLAY_ONLY',source_sha:execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),sourceHashes,snapshot_edits:edits,original_api_fallback:false,storage_key:'woofi.acceptance.watchlist.v1',fixture_clock:dataset.clock,evidence:Object.fromEntries(['annual','quarterly','ttm'].map(f=>{const file=path.resolve(evidenceDir,`FPT-${f}-saved-replay.json`);return [path.basename(file),hash(file)];})),dataset_sha256:hash(path.join(output,'replay-data.json'))};
fs.writeFileSync(path.join(output,'ACCEPTANCE_MANIFEST.json'),JSON.stringify(manifest,null,2));
fs.writeFileSync(path.join(output,'START_INSTRUCTIONS.txt'),`After separately authorizing and gracefully stopping only the existing 3410 development preview:\nSet-Location -LiteralPath '${output}'\nnpm.cmd start -- --port 3410\nOpen http://127.0.0.1:3410/demo/acceptance\nDo not start a backend or Collector. No production ports, state or data are used.\n`);
console.log(JSON.stringify({snapshot:output,source_sha:manifest.source_sha,api:'OFFLINE_REPLAY_ONLY',build:'npm.cmd run build -- --webpack',launch:'NOT PERFORMED'}));
