// Run only under the installed Desktop's Electron Node runtime. No Host or LLM starts.
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

async function main() {
  const request = JSON.parse(process.argv[2]);
  const runtime = path.join(path.dirname(process.execPath), 'resources', 'app.asar', 'dsh');
  const desktopRequire = createRequire(path.join(runtime, 'package.json'));
  const version = JSON.parse(fs.readFileSync(
    path.join(runtime, 'node_modules', '@deepseek-ai', 'dsh', 'package.json'), 'utf8',
  )).version;
  const { Context } = desktopRequire('@deepseek-ai/cordis');
  const { FileSystemSkillProvider } = desktopRequire('@deepseek-ai/dsh-skill-filesystem');
  const context = new Context();
  const abort = new AbortController();
  const provider = new FileSystemSkillProvider(context, {
    signal: abort.signal, invalidate() {},
  }, {
    providerName: 'agent-marketplace-inspection',
    includeDefaultRoots: request.includeDefaultRoots ?? false,
    dshHome: request.dshHome,
    customSkillDirs: request.roots,
    watch: false,
  });
  try {
    const listed = await provider.list({});
    if (!Array.isArray(listed)) throw new Error('Incomplete Desktop skill discovery');
    const skills = [];
    for (const candidate of listed) {
      const loaded = await provider.get(candidate, {});
      if (!loaded) throw new Error(`Cannot load skill: ${candidate.name}`);
      skills.push({ name: loaded.name, invocation: loaded.invocation, path: loaded.path });
    }
    process.stdout.write(`DSH_INSPECTION:${JSON.stringify({ version, skills })}\n`);
  } finally {
    abort.abort();
    await provider.dispose();
  }
}

main().catch(error => {
  process.stderr.write(`Desktop skill inspection failed: ${error.message}\n`);
  process.exitCode = 1;
});
