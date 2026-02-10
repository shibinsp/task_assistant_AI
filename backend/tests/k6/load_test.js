import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// ==================== Configuration ====================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API = `${BASE_URL}/api/v1`;
const EMAIL = __ENV.EMAIL || 'admin@acme.com';
const PASSWORD = __ENV.PASSWORD || 'demo123';

// Custom metrics per group
const healthDuration = new Trend('health_duration', true);
const authDuration = new Trend('auth_duration', true);
const tasksDuration = new Trend('tasks_duration', true);
const chatDuration = new Trend('chat_duration', true);
const checkinsDuration = new Trend('checkins_duration', true);
const skillsDuration = new Trend('skills_duration', true);
const reportsDuration = new Trend('reports_duration', true);
const agentsDuration = new Trend('agents_duration', true);
const predictionsDuration = new Trend('predictions_duration', true);
const workforceDuration = new Trend('workforce_duration', true);
const aiUnblockDuration = new Trend('ai_unblock_duration', true);
const knowledgeDuration = new Trend('knowledge_duration', true);
const orgsDuration = new Trend('orgs_duration', true);
const integrationsDuration = new Trend('integrations_duration', true);
const usersDuration = new Trend('users_duration', true);
const errorRate = new Rate('errors');
const requestCount = new Counter('total_requests');

// ==================== Test Scenarios ====================

const SCENARIO = __ENV.SCENARIO || 'load';

const scenarios = {
  smoke: {
    vus: 1,
    duration: '30s',
    thresholds: {
      http_req_duration: ['p(95)<2000'],
      'http_req_duration{group:::01_Health}': ['p(95)<200'],
      'http_req_duration{group:::02_Auth}': ['p(95)<300'],
      'http_req_duration{group:::03_Tasks}': ['p(95)<500'],
      http_req_failed: ['rate<0.1'],
    },
  },
  load: {
    stages: [
      { duration: '10s', target: 5 },
      { duration: '40s', target: 10 },
      { duration: '10s', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<5000'],
      'http_req_duration{group:::01_Health}': ['p(95)<200'],
      'http_req_duration{group:::02_Auth}': ['p(95)<500'],
      'http_req_duration{group:::03_Tasks}': ['p(95)<500'],
      http_req_failed: ['rate<0.05'],
    },
  },
  stress: {
    stages: [
      { duration: '20s', target: 10 },
      { duration: '40s', target: 30 },
      { duration: '40s', target: 30 },
      { duration: '20s', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<10000'],
      'http_req_duration{group:::01_Health}': ['p(95)<500'],
      http_req_failed: ['rate<0.1'],
    },
  },
  spike: {
    stages: [
      { duration: '10s', target: 1 },
      { duration: '5s', target: 50 },
      { duration: '30s', target: 50 },
      { duration: '10s', target: 1 },
      { duration: '5s', target: 0 },
    ],
    thresholds: {
      http_req_duration: ['p(95)<15000'],
      http_req_failed: ['rate<0.15'],
    },
  },
};

const selectedScenario = scenarios[SCENARIO] || scenarios.load;

export const options = {
  vus: selectedScenario.vus,
  duration: selectedScenario.duration,
  stages: selectedScenario.stages,
  thresholds: {
    ...selectedScenario.thresholds,
    errors: ['rate<0.1'],
  },
};

// ==================== Helpers ====================

const headers = (token) => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${token}`,
});

function jsonBody(obj) {
  return JSON.stringify(obj);
}

// ==================== Setup ====================

export function setup() {
  // Login to get token
  const loginRes = http.post(
    `${API}/auth/login`,
    jsonBody({ email: EMAIL, password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const success = check(loginRes, {
    'setup: login status 200': (r) => r.status === 200,
    'setup: has access token': (r) => {
      try {
        return r.json().tokens.access_token !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    console.error(`Login failed: ${loginRes.status} - ${loginRes.body}`);
    return { token: '', userId: '' };
  }

  const data = loginRes.json();
  const token = data.tokens.access_token;
  const userId = data.user.id;

  // Get a task ID for later tests
  const tasksRes = http.get(`${API}/tasks`, { headers: headers(token) });
  let taskId = '';
  try {
    const items = tasksRes.json().items;
    if (items && items.length > 0) {
      taskId = items[0].id;
    }
  } catch (e) {
    // no tasks available
  }

  console.log(`Setup complete: user=${EMAIL}, taskId=${taskId ? taskId.substring(0, 8) : 'none'}`);
  return { token, userId, taskId };
}

// ==================== Main Test ====================

export default function (data) {
  const { token, userId, taskId } = data;

  if (!token) {
    console.error('No token available, skipping iteration');
    errorRate.add(1);
    return;
  }

  const h = headers(token);

  // --- 1. Health (no auth) ---
  group('01_Health', () => {
    const res = http.get(`${BASE_URL}/health`);
    healthDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'health: status 200': (r) => r.status === 200,
      'health: status healthy': (r) => {
        try { return r.json().status === 'healthy'; } catch (e) { return false; }
      },
    });
    errorRate.add(!ok);
  });

  // --- 2. Auth ---
  group('02_Auth', () => {
    const meRes = http.get(`${API}/auth/me`, { headers: h });
    authDuration.add(meRes.timings.duration);
    requestCount.add(1);
    const ok = check(meRes, {
      'auth/me: status 200': (r) => r.status === 200,
      'auth/me: has email': (r) => {
        try { return r.json().email !== undefined; } catch (e) { return false; }
      },
    });
    errorRate.add(!ok);
  });

  // --- 3. Tasks ---
  group('03_Tasks', () => {
    // List tasks
    const listRes = http.get(`${API}/tasks`, { headers: h });
    tasksDuration.add(listRes.timings.duration);
    requestCount.add(1);
    let ok = check(listRes, {
      'tasks list: status 200': (r) => r.status === 200,
      'tasks list: valid response': (r) => {
        try { const d = r.json(); return d.items !== undefined || d.tasks !== undefined || Array.isArray(d); } catch (e) { return false; }
      },
    });
    errorRate.add(!ok);

    // Create task
    const createRes = http.post(
      `${API}/tasks`,
      jsonBody({
        title: `K6 Load Test Task ${Date.now()}`,
        description: 'Created during k6 load testing',
        priority: 'medium',
      }),
      { headers: h }
    );
    tasksDuration.add(createRes.timings.duration);
    requestCount.add(1);
    ok = check(createRes, {
      'task create: status 201': (r) => r.status === 201,
    });
    errorRate.add(!ok);

    // Get specific task
    if (taskId) {
      const getRes = http.get(`${API}/tasks/${taskId}`, { headers: h });
      tasksDuration.add(getRes.timings.duration);
      requestCount.add(1);
      ok = check(getRes, {
        'task get: status 200': (r) => r.status === 200,
      });
      errorRate.add(!ok);
    }
  });

  // --- 4. Chat (AI) ---
  group('04_Chat_AI', () => {
    // Send chat message
    const chatRes = http.post(
      `${API}/chat`,
      jsonBody({ message: 'What are my top priorities today?' }),
      { headers: h, timeout: '30s' }
    );
    chatDuration.add(chatRes.timings.duration);
    requestCount.add(1);
    let ok = check(chatRes, {
      'chat send: status 200': (r) => r.status === 200,
      'chat send: has content': (r) => {
        try { return r.json().message.content.length > 0; } catch (e) { return false; }
      },
    });
    errorRate.add(!ok);

    // List conversations
    const convRes = http.get(`${API}/chat/conversations`, { headers: h });
    chatDuration.add(convRes.timings.duration);
    requestCount.add(1);
    ok = check(convRes, {
      'chat conversations: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 5. Check-ins ---
  group('05_Checkins', () => {
    const res = http.get(`${API}/checkins`, { headers: h });
    checkinsDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'checkins list: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 6. Skills ---
  group('06_Skills', () => {
    const res = http.get(`${API}/skills`, { headers: h });
    skillsDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'skills list: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 7. Reports ---
  group('07_Reports', () => {
    const res = http.get(`${API}/reports/dashboard`, { headers: h });
    reportsDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'reports dashboard: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 8. Agents ---
  group('08_Agents', () => {
    // List agents
    const listRes = http.get(`${API}/agents`, { headers: h });
    agentsDuration.add(listRes.timings.duration);
    requestCount.add(1);
    let ok = check(listRes, {
      'agents list: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);

    // Agent stats
    const statsRes = http.get(`${API}/agents/stats`, { headers: h });
    agentsDuration.add(statsRes.timings.duration);
    requestCount.add(1);
    ok = check(statsRes, {
      'agents stats: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);

    // Recommendations
    const recRes = http.get(`${API}/agents/recommendations`, { headers: h });
    agentsDuration.add(recRes.timings.duration);
    requestCount.add(1);
    ok = check(recRes, {
      'agents recommendations: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 9. Predictions ---
  group('09_Predictions', () => {
    const accRes = http.get(`${API}/predictions/accuracy`, { headers: h });
    predictionsDuration.add(accRes.timings.duration);
    requestCount.add(1);
    let ok = check(accRes, {
      'predictions accuracy: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);

    const hireRes = http.get(`${API}/predictions/hiring`, { headers: h });
    predictionsDuration.add(hireRes.timings.duration);
    requestCount.add(1);
    ok = check(hireRes, {
      'predictions hiring: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 10. Workforce ---
  group('10_Workforce', () => {
    const res = http.get(`${API}/workforce/scores`, { headers: h });
    workforceDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'workforce scores: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 11. AI Unblock ---
  group('11_AI_Unblock', () => {
    const res = http.post(
      `${API}/ai/unblock`,
      jsonBody({
        query: 'How to fix async database connection timeout?',
        blocker_type: 'technical',
        skill_level: 'intermediate',
      }),
      { headers: h, timeout: '30s' }
    );
    aiUnblockDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'ai unblock: status 200': (r) => r.status === 200,
      'ai unblock: has suggestion': (r) => {
        try { return r.json().suggestion.length > 0; } catch (e) { return false; }
      },
    });
    errorRate.add(!ok);
  });

  // --- 12. Knowledge Base ---
  group('12_Knowledge_Base', () => {
    const res = http.get(`${API}/ai/knowledge-base/documents`, { headers: h });
    knowledgeDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'knowledge base: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 13. Organizations ---
  group('13_Organizations', () => {
    const res = http.get(`${API}/organizations/current`, { headers: h });
    orgsDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'org current: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 14. Integrations ---
  group('14_Integrations', () => {
    const res = http.get(`${API}/integrations`, { headers: h });
    integrationsDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'integrations list: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // --- 15. Users ---
  group('15_Users', () => {
    const res = http.get(`${API}/users`, { headers: h });
    usersDuration.add(res.timings.duration);
    requestCount.add(1);
    const ok = check(res, {
      'users list: status 200': (r) => r.status === 200,
    });
    errorRate.add(!ok);
  });

  // Pause between iterations to simulate real user behavior
  sleep(1);
}

// ==================== Teardown ====================

export function teardown(data) {
  console.log('Load test complete.');
}
