// Opt-in integration checks against the installed Kimi Code Desktop bundle.
// Runs its unmodified install, manifest and Skill discovery functions in a VM;
// never starts the desktop app, reads credentials, or contacts a model.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const ROOT = path.resolve(__dirname, '..');
const ASAR = process.env.KIMI_CODE_TEST_ASAR;
const ONLINE = process.env.KIMI_CODE_TEST_GITHUB === '1';
const groups = ['common-workflow', 'frontend-dev', 'backend-dev', 'testing-automation', 'agent-manager'];

function runtime(asar) {
  const fd = fs.openSync(asar, 'r');
  let bundle;
  let bundlerRuntime;
  try {
    const prefix = Buffer.alloc(16);
    fs.readSync(fd, prefix, 0, 16, 0);
    const dataOffset = 8 + prefix.readUInt32LE(4);
    const buffer = Buffer.alloc(prefix.readUInt32LE(12));
    fs.readSync(fd, buffer, 0, buffer.length, 16);
    const header = JSON.parse(buffer.toString('utf8'));
    const read = (entry) => {
      assert.equal(entry.unpacked, undefined, 'Expected an ASAR-contained runtime');
      const bytes = Buffer.alloc(entry.size);
      fs.readSync(fd, bytes, 0, bytes.length, dataOffset + Number(entry.offset));
      return bytes.toString('utf8');
    };
    assert.equal(JSON.parse(read(header.files['package.json'])).version, '1.0.4',
      'A new Kimi runtime needs fresh integration evidence');
    const helpers = Object.entries(header.files.out.files).find(([name]) => name.startsWith('rolldown-runtime-'));
    assert.ok(helpers, 'Bundler infrastructure not found');
    const module = { exports: {} };
    vm.runInNewContext(read(helpers[1]), { module, exports: module.exports });
    bundlerRuntime = module.exports;
    bundle = Object.entries(header.files.out.files)
      .filter(([name, entry]) => name.endsWith('.cjs') && entry.size > 2_000_000)
      .map(([, entry]) => read(entry))
      .find((text) => text.includes('async function parseManifest(pluginRoot)'));
    assert.ok(bundle, 'Kimi plugin runtime not found');
  } finally {
    fs.closeSync(fd);
  }
  const region = (suffix) => {
    const marker = bundle.split('\n').find((line) => line.startsWith('//#region ') && line.endsWith(suffix));
    assert.ok(marker, `Runtime region missing: ${suffix}`);
    const start = bundle.indexOf(marker);
    const end = bundle.indexOf('//#endregion', start);
    assert.ok(end > start);
    return bundle.slice(start + marker.length, end);
  };
  // Only infrastructure imports and unused DI decoration are supplied here.
  // Parsing, YAML, paths, file traversal, installation and persistence are real.
  const context = vm.createContext({
    node_fs: fs, node_fs_promises: fsp, node_path: { default: path }, node_os: os,
    process: { platform: process.platform, cwd: () => ROOT, versions: process.versions, nextTick: process.nextTick },
    require: (name) => {
      assert.ok(['fs', 'util', 'stream', 'events', 'zlib'].includes(name), `Unexpected runtime import: ${name}`);
      return require(name);
    },
    require_rolldown_runtime: bundlerRuntime,
    node_stream_promises: require('node:stream/promises'),
    fetch: ONLINE ? fetch : () => { throw new Error('Network disabled in local fixture'); },
    AbortController, AbortSignal, setTimeout, clearTimeout, setImmediate, clearImmediate,
    URL, Buffer, ErrorCodes: { VALIDATION_FAILED: 'validation_failed', PLUGIN_LOAD_FAILED: 'plugin_load_failed' },
    SkillErrors: { codes: { SKILL_PARSE_FAILED: 'skill_parse_failed', SKILL_TYPE_UNSUPPORTED: 'skill_type_unsupported' } },
    ILogService: {}, __decorateParam: () => () => {},
  });
  const discoveryStart = bundle.indexOf('function isSkillScanExcludedEntry(entryName)');
  assert.ok(discoveryStart > 0);
  const discovery = bundle.slice(discoveryStart, bundle.indexOf('//#endregion', discoveryStart));
  const code = [
    region('/_base/errors/errors.ts'),
    region('/pathe/dist/shared/pathe.M-eThtNZ.mjs'), region('/pathe/dist/index.mjs'),
    region('/js-yaml/dist/js-yaml.mjs'), region('/_base/text/frontmatter.ts'),
    region('/features/skill/catalog/types.ts'), region('/features/skill/catalog/parser.ts'),
    region('/_base/utils/xml-escape.ts'), region('/features/skill/catalog/registry.ts'),
    region('/pend/index.js'), region('/yauzl/fd-slicer.js'), region('/yauzl/crc32.js'),
    region('/os/backends/node-local/tools/rgLocator.ts'),
    region('/helpers/esm/decorate.js').split('function isSkillScanExcludedEntry')[0], discovery,
    region('/app/plugin/types.ts'), region('/app/plugin/manifest.ts'),
    region('/app/plugin/store.ts'), region('/app/plugin/source.ts'), region('/app/plugin/manager.ts'),
    region('/app/plugin/github-resolver.ts'), region('/app/plugin/archive.ts'),
    'globalThis.kimi = {PluginManager, parseManifest, discoverFileSkills, resolveInstallSource, summarizeSkill, isUserActivatableSkillType, InMemorySkillCatalog};',
  ].join('\n');
  vm.runInContext(code, context, { timeout: 10_000, filename: 'installed-kimi-plugin-runtime.cjs' });
  return context.kimi;
}

test('Kimi native plugin compatibility', { skip: !ASAR, timeout: 60_000 }, async (t) => {
  const kimi = runtime(ASAR);
  const temporary = await fsp.mkdtemp(path.join(os.tmpdir(), 'agent-marketplace-kimi-'));
  try {
    const source = path.join(temporary, 'source');
    await fsp.mkdir(source);
    for (const group of groups) {
      await fsp.cp(path.join(ROOT, 'plugins', group), path.join(source, 'plugins', group), { recursive: true });
    }
    const rootManifest = path.join(ROOT, 'kimi.plugin.json');
    if (fs.existsSync(rootManifest)) await fsp.copyFile(rootManifest, path.join(source, 'kimi.plugin.json'));
    const home = path.join(temporary, 'user');
    const manager = new kimi.PluginManager({ kimiHomeDir: home });
    await manager.load();

    await t.test('whole repository installs and discovers all 16 shared Skills', async () => {
      const record = await manager.install(source);
      assert.equal(record.id, 'agent-marketplace');
      assert.equal(record.state, 'ok');
      assert.equal(record.skillCount, 16);
      assert.equal(record.diagnostics.length, 0);
      assert.equal(record.manifest.interface.displayName, 'Agent Marketplace');
      assert.equal(record.manifest.mcpServers, undefined);
      assert.equal(record.manifest.hooks, undefined);
      assert.equal(record.manifest.sessionStart, undefined);
      const discovery = await kimi.discoverFileSkills(manager.pluginSkillRoots());
      assert.equal(discovery.skills.length, 16);
      assert.equal(new Set(discovery.skills.map((skill) => skill.name.toLowerCase())).size, 16);
      const manual = new Set(['handoff', 'resolve-conflicts', 'check-updates', 'configure-project']);
      const catalog = new kimi.InMemorySkillCatalog();
      for (const skill of discovery.skills) {
        catalog.register(skill);
        assert.equal(skill.metadata.disableModelInvocation === true, manual.has(skill.name), skill.name);
        assert.equal(kimi.summarizeSkill(skill).disableModelInvocation === true, manual.has(skill.name));
        assert.equal(kimi.isUserActivatableSkillType(skill.metadata.type), true);
        const relative = path.relative(record.root, skill.path);
        assert.ok(!relative.startsWith('..'));
        assert.deepEqual(await fsp.readFile(skill.path), await fsp.readFile(path.join(ROOT, relative)));
        assert.ok(catalog.renderSkillPrompt(skill, '', {}).includes(skill.content));
      }
      assert.equal(catalog.listSkills().length, 16);
      assert.equal(catalog.listInvocableSkills().length, 12);
      for (const name of manual) {
        assert.ok(catalog.getSkill(name.toUpperCase()));
        assert.equal(catalog.listInvocableSkills().some((skill) => skill.name === name), false);
      }
      // Companion scripts, references and licenses also survive managed copying.
      for (const relative of [
        'plugins/agent-manager/references/kimi.md',
        'plugins/agent-manager/skills/configure-project/scripts/configure_project.py',
        'plugins/common-workflow/skills/writing-for-agents/SKILL-MECHANICS.md',
        'plugins/backend-dev/skills/java-spring-boot/assets/schema.json',
      ]) {
        assert.deepEqual(await fsp.readFile(path.join(record.root, relative)), await fsp.readFile(path.join(ROOT, relative)));
      }
      const receipt = JSON.parse(await fsp.readFile(path.join(home, 'plugins/installed.json'), 'utf8'));
      assert.equal(receipt.plugins[0].originalSource, source);
      assert.equal(receipt.plugins[0].source, 'local-path');
      assert.equal(receipt.plugins[0].root, record.root);
      await manager.setEnabled(record.id, false);
      assert.equal(manager.pluginSkillRoots().length, 0);
      await manager.load();
      assert.equal(manager.pluginSkillRoots().length, 0);
      await manager.setEnabled(record.id, true);
      assert.equal((await kimi.discoverFileSkills(manager.pluginSkillRoots())).skills.length, 16);
    });

    await t.test('five local categories install independently', async () => {
      const separate = new kimi.PluginManager({ kimiHomeDir: path.join(temporary, 'categories') });
      await separate.load();
      const counts = [5, 4, 1, 3, 3];
      for (let i = 0; i < groups.length; i++) {
        const record = await separate.install(path.join(source, 'plugins', groups[i]));
        assert.equal(record.id, groups[i]);
        assert.equal(record.state, 'ok');
        assert.equal(record.diagnostics.length, 0);
        assert.equal(record.skillCount, counts[i]);
      }
      assert.equal((await kimi.discoverFileSkills(separate.pluginSkillRoots())).skills.length, 16);
    });

    await t.test('missing manifest and SSH address reproduce the screenshot errors', async () => {
      const missing = path.join(temporary, 'missing');
      await fsp.mkdir(missing);
      await assert.rejects(manager.install(missing), /No manifest at kimi\.plugin\.json or \.kimi-plugin\/plugin\.json/);
      assert.throws(() => kimi.resolveInstallSource('git@github.com:vsattce/agent-marketplace.git'), /Plugin root must be an absolute path/);
      const github = kimi.resolveInstallSource('https://github.com/vsattce/agent-marketplace.git');
      assert.equal(github.kind, 'github');
      assert.equal(github.owner, 'vsattce');
      assert.equal(github.repo, 'agent-marketplace');
      const main = kimi.resolveInstallSource('https://github.com/vsattce/agent-marketplace/tree/main');
      assert.equal(main.ref.value, 'main');
    });

    await t.test('published HTTPS repository installs using the native GitHub download path', { skip: !ONLINE }, async () => {
      const published = new kimi.PluginManager({ kimiHomeDir: path.join(temporary, 'github') });
      await published.load();
      const record = await published.install('https://github.com/vsattce/agent-marketplace.git');
      assert.equal(record.id, 'agent-marketplace');
      assert.equal(record.state, 'ok');
      assert.equal(record.diagnostics.length, 0);
      assert.equal(record.source, 'github');
      assert.match(record.github.installedSha, /^[0-9a-f]{40}$/);
      assert.equal(record.skillCount, 16);
      assert.deepEqual(await fsp.readFile(path.join(record.root, 'kimi.plugin.json')), await fsp.readFile(rootManifest));
    });
  } finally {
    // Recursive cleanup is restricted to this freshly allocated fixture root.
    const resolved = await fsp.realpath(temporary);
    assert.equal(path.dirname(resolved), await fsp.realpath(os.tmpdir()));
    assert.ok(path.basename(resolved).startsWith('agent-marketplace-kimi-'));
    await fsp.rm(resolved, { recursive: true, force: true });
  }
});
