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
  fetch(`${buildUrl}/build`, {
    method: 'POST',
    Accept: 'application/json',
    'Content-Type': 'application/json',
    body: JSON.stringify(data)
  })
    .then(async r => {
      let text = await r.text();
      console.error(text)
      if (r.status !== 200) {
        throw new Error(text);
      }
      return text;
    })
    .then(r => r.text())
    .then(async taskId => {
      console.log(new Date())
      console.log(taskId)
      // wait for 15 minutes, checking the task status
      while (new Date() - startTime < 2 * 1000) {
        fetch(`${buildUrl}/tasks/${taskId}/task.log`).then(taskLog => {
          console.log(new Date())
          console.log(taskLog)
        })
        console.log('waiting for build to finish...')
        await new Promise(r3 => setTimeout(r3, 1000))
      }
    })


} catch (error) {
  core.setFailed(error.message);
}

