const core = require('@actions/core');
const github = require('@actions/github');

// How long to wait for the build to finish before giving up.
const waitTime = 15 * 60 * 1000;

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
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
  })
    .then(async r => {
      let text = await r.json();
      console.error(text)
      if (r.status !== 200) {
        throw new Error(text);
      }
      return text;
    })
    .then(r => {
      return r.task_id
    })
    .then(async taskId => {
      console.log(new Date())
      console.log(taskId)
      // wait for 15 minutes, checking the task status
      while (new Date() - startTime < waitTime) {
        const taskLogData = await fetch(`${buildUrl}/tasks/${taskId}/task.log`).then(r => r.text())
        console.log(new Date())
        if (taskLogData.includes('Success.')) {
          core.setOutput('build_status', 'success')
          console.log("DONE")
          return
        }
        if (taskLogData.includes('Failed.')) {
          core.setOutput('build_status', 'failed')
          core.setFailed(taskLogData);
          return
        }
        console.log('waiting for build to finish...')
        await new Promise(r3 => setTimeout(r3, 1000))
      }
      core.setFailed(`Waited ${waitTime / 1000} seconds and the build didn't finish. Giving up.`);
    })


} catch (error) {
  core.setFailed(error.message);
}

