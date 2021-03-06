import hudson.FilePath
import hudson.model.*

def toolbox = extension."build-flow-toolbox"
def sha1 = build.environment.get("ghprbActualCommit")
def branch = build.environment.get("ghprbSourceBranch")
def subsetJob = build.environment.get("SUBSET_JOB") ?: "edx-platform-test-subset"
def repoName = build.environment.get("REPO_NAME") ?: "edx-platform"
def coverageJob = build.environment.get("COVERAGE_JOB") ?: "edx-platform-unit-coverage"
def workerLabel = build.environment.get("WORKER_LABEL") ?: "jenkins-worker"
def djangoVersion = build.environment.get("DJANGO_VERSION") ?: " "
def targetBranch = build.environment.get("TARGET_BRANCH") ?: "origin/master"

// Any environment variables that you want to inject into the environment of
// child jobs of this build flow should be added here (comma-separated,
// in the format VARIABLE=VALUE)
def envVarString = "DJANGO_VERSION=${djangoVersion}"

guard{
    unit = parallel(
      {
        lms_unit_1 = build(subsetJob,
                           sha1: sha1,
                           SHARD: "1",
                           TEST_SUITE: "lms-unit",
                           PARENT_BUILD: "PR Build #" + build.number,
                           WORKER_LABEL: workerLabel,
                           ENV_VARS: envVarString
                           )
        toolbox.slurpArtifacts(lms_unit_1)
      },
      {
        lms_unit_2 = build(subsetJob,
                           sha1: sha1, 
                           SHARD: "2", 
                           TEST_SUITE: "lms-unit",
                           PARENT_BUILD: "PR Build #" + build.number,
                           WORKER_LABEL: workerLabel, 
                           ENV_VARS: envVarString
                           )
        toolbox.slurpArtifacts(lms_unit_2)
      },
      {
        lms_unit_3 = build(subsetJob, 
                           sha1: sha1,
                           SHARD: "3", 
                           TEST_SUITE: "lms-unit",
                           PARENT_BUILD: "PR Build #" + build.number,
                           WORKER_LABEL: workerLabel,
                           ENV_VARS: envVarString
                           )
        toolbox.slurpArtifacts(lms_unit_3)
      },
      {
        lms_unit_4 = build(subsetJob,
                           sha1: sha1,
                           SHARD: "4",
                           TEST_SUITE: "lms-unit",
                           PARENT_BUILD: "PR Build #" + build.number,
                           WORKER_LABEL: workerLabel,
                           ENV_VARS: envVarString
                           )
        toolbox.slurpArtifacts(lms_unit_4)
      },
      {
        cms_unit = build(subsetJob,
                         sha1: sha1,
                         SHARD: "1",
                         TEST_SUITE: "cms-unit",
                         PARENT_BUILD: "PR Build #" + build.number,
                         WORKER_LABEL: workerLabel,
                         ENV_VARS: envVarString
                         )
        toolbox.slurpArtifacts(cms_unit)
      },
      {
        commonlib_unit = build(subsetJob,
                               sha1: sha1,
                               SHARD: "1", 
                               TEST_SUITE: "commonlib-unit",
                               PARENT_BUILD: "PR Build #" + build.number,
                               WORKER_LABEL: workerLabel, 
                               ENV_VARS: envVarString
                               )
        toolbox.slurpArtifacts(commonlib_unit)
      },
    )

    check_coverage = (
      lms_unit_1.result.toString() == 'SUCCESS' &&
      lms_unit_2.result.toString() == 'SUCCESS' &&
      lms_unit_3.result.toString() == 'SUCCESS' &&
      lms_unit_4.result.toString() == 'SUCCESS' &&
      cms_unit.result.toString() == 'SUCCESS' &&
      commonlib_unit.result.toString() == 'SUCCESS')

    if (check_coverage){
      unit_coverage = build(coverageJob,
                            UNIT_BUILD_NUM_1: commonlib_unit.number,
                            UNIT_BUILD_NUM_2: lms_unit_1.number,
                            UNIT_BUILD_NUM_3: lms_unit_2.number,
                            UNIT_BUILD_NUM_4: lms_unit_3.number,
                            UNIT_BUILD_NUM_5: lms_unit_4.number,
                            UNIT_BUILD_NUM_6: cms_unit.number,
                            sha1: sha1,
                            PARENT_BUILD: "PR Build #" + build.number,
                            CI_BRANCH: branch,
                            TARGET_BRANCH: targetBranch
                           )

      toolbox.slurpArtifacts(unit_coverage)
    }
}rescue{
    FilePath artifactsDir =  new FilePath(build.artifactManager.getArtifactsDir())
    FilePath copyToDir = new FilePath(build.workspace, repoName)
    artifactsDir.copyRecursiveTo(copyToDir)

    // Delete the report artifacts that we copied into the staging area, to reduce
    // disk usage. These are copied by the HTML Publisher plugin and the
    // Shining Panda Coverage plugin, and these are redundant. However, leave
    // the 'test_root' directory, as it is indexed by Splunk for paver timing
    // reports
    List toDelete = artifactsDir.list().findAll { item ->
        item.getName() != 'test_root' 
    }
    toDelete.each { item ->
        if (item.isDirectory()) {
            item.deleteRecursive()
        } else {
            item.delete()
        }
    }

}
