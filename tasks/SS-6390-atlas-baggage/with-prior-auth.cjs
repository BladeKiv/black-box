const assert = require('node:assert/strict');
for (const name of ['BOOKING_USERNAME', 'BOOKING_PASSWORD']) {
  assert(process.env[name], `Missing required environment variable: ${name}`);
}
require('./run-flow.cjs');
