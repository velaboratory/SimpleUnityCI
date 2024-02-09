const core = require('@actions/core');
const github = require('@actions/github');

try {
  const buildUrl = core.getInput('build_server');
  const data = {
    git_repo: core.getInput('git_repo'),
    branch: core.getInput('branch'),
    build_target: core.getInput('build_target'),
    keystore_name: core.getInput('keystore_name'),
    keystore_pass: core.getInput('keystore_pass'),
    keyalias_name: core.getInput('keyalias_name'),
    keyalias_pass: core.getInput('keyalias_pass'),
    oculus_app_id: core.getInput('oculus_app_id'),
    oculus_app_secret: core.getInput('oculus_app_secret'),
    oculus_release_channel: core.getInput('oculus_release_channel'),
  }
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

