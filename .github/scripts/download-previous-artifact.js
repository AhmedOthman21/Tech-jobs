
const fs = require('fs');
const { execSync } = require('child_process');

module.exports = async ({ github, context, core }) => {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const workflowFilename = process.env.WORKFLOW_FILENAME;
  const artifactName = process.env.ARTIFACT_NAME;
  const artifactFilename = process.env.ARTIFACT_FILENAME;
  const unzipDir = process.env.UNZIP_DIR;
  const branchRef = context.ref || '';
  const branch = branchRef.startsWith('refs/heads/') ? branchRef.substring('refs/heads/'.length) : branchRef;

  try {
    // Retrieve the list of workflows
    const workflows = await github.rest.actions.listRepoWorkflows({ owner, repo });
    const workflow = workflows.data.workflows.find(w => w.path.endsWith(workflowFilename));

    if (!workflow) {
      core.setFailed(`Workflow file ${workflowFilename} not found.`);
      return;
    }

    // Retrieve the list of workflow runs (latest successful on the same branch)
    const runs = await github.rest.actions.listWorkflowRuns({
      owner,
      repo,
      workflow_id: workflow.id,
      status: 'success',
      branch,
      per_page: 1
    });

    if (runs.data.total_count === 0) {
      core.setFailed('No successful workflow runs found.');
      return;
    }

    const runId = runs.data.workflow_runs[0].id;

    // Retrieve the list of artifacts for the latest successful run
    const artifacts = await github.rest.actions.listWorkflowRunArtifacts({ owner, repo, run_id: runId });
    const artifact = artifacts.data.artifacts.find(a => a.name === artifactName);

    if (!artifact) {
      core.setFailed(`Artifact ${artifactName} not found.`);
      return;
    }

    // Download the artifact
    const response = await github.rest.actions.downloadArtifact({
      owner,
      repo,
      artifact_id: artifact.id,
      archive_format: 'zip'
    });

    fs.writeFileSync(artifactFilename, Buffer.from(response.data));
    execSync(`unzip -o ${artifactFilename} -d ${unzipDir}`);

    // Simple debug: confirm host file line count after extraction
    const hostFile = 'posted_jobs.txt';
    if (fs.existsSync(hostFile)) {
      const lines = fs.readFileSync(hostFile, 'utf8').split('\n').filter(Boolean).length;
      core.info(`posted_jobs.txt extracted with ${lines} lines on host.`);
    } else {
      core.info('posted_jobs.txt not found after extraction.');
    }

    console.log('Artifact downloaded and extracted successfully.');
  } catch (error) {
    core.setFailed(`Error downloading artifact: ${error.message}`);
  }
};
