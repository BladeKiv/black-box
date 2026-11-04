// Transfer browser-selected requests through memory; remove the encrypted temporary input immediately.
const fs = require('node:fs');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const file = require('node:path').join(__dirname, 'runtime-input.enc');
const bundle = fs.readFileSync(file);
fs.unlinkSync(file);
const cipher = crypto.createDecipheriv('aes-256-gcm', bundle.subarray(0, 32), bundle.subarray(32, 44));
cipher.setAuthTag(bundle.subarray(44, 60));
const data = JSON.parse(Buffer.concat([cipher.update(bundle.subarray(60)), cipher.final()]).toString('utf8'));
const all = process.argv.includes('--all');
const remaining = all ? data : data.filter(x => x.request.additionalInfo.pnrCode !== 'ER0XZ8');
require('node:assert/strict').equal(remaining.length, all ? 4 : 3);
const result = spawnSync('python', ['-B', require('node:path').join(__dirname, 'retrieve.py'), ...(all ? [] : ['--append'])], {input: JSON.stringify(remaining), encoding: 'utf8', windowsHide: true});
process.stdout.write(result.stdout || '');
process.stderr.write(result.stderr || '');
process.exit(result.status ?? 1);
