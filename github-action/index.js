const core = require('@actions/core');
const github = require('@actions/github');

try {
  const buildUrl = core.getInput('url');
  const data = core.getInput('data');
  console.log(buildUrl);
  console.log(data);
  const startTime = new Date();
  console.log(startTime)
  const r = fetch(buildUrl, { method: 'POST', body: data }).then(r => r.json()).then(r => {
    console.log(new Date())
    console.log(r)
  })
} catch (error) {
  core.setFailed(error.message);
}

