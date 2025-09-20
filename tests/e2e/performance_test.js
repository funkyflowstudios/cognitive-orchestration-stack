// k6 performance test script for Cognitive Orchestration Stack
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 }, // Ramp up to 10 users
    { duration: '1m', target: 10 },  // Stay at 10 users
    { duration: '30s', target: 20 }, // Ramp up to 20 users
    { duration: '1m', target: 20 },  // Stay at 20 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests should be below 1s
    http_req_failed: ['rate<0.1'],     // Error rate should be below 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Test health endpoints
  let response = http.get(`${BASE_URL}/health/live`);
  check(response, {
    'health live status is 200': (r) => r.status === 200,
    'health live response time < 500ms': (r) => r.timings.duration < 500,
  });

  response = http.get(`${BASE_URL}/health/ready`);
  check(response, {
    'health ready status is 200': (r) => r.status === 200,
    'health ready response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  // Test metrics endpoint
  response = http.get(`${BASE_URL}/metrics/`);
  check(response, {
    'metrics status is 200': (r) => r.status === 200,
    'metrics response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  // Test metrics dashboard
  response = http.get(`${BASE_URL}/metrics/dashboard`);
  check(response, {
    'metrics dashboard status is 200': (r) => r.status === 200,
    'metrics dashboard response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  // Test API documentation
  response = http.get(`${BASE_URL}/docs`);
  check(response, {
    'docs status is 200': (r) => r.status === 200,
    'docs response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  // Test CORS headers
  response = http.get(`${BASE_URL}/health/live`, {
    headers: { 'Origin': 'http://localhost:3000' }
  });
  check(response, {
    'CORS headers present': (r) => r.headers['Access-Control-Allow-Origin'] === '*',
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'performance-results.json': JSON.stringify(data, null, 2),
  };
}
