import sys
import logging
import os

import click
from github import Github

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

DB_CACHE_FILEPATH = 'common/test/db_cache'

BOKCHOY_DB_FILES = [
    'bok_choy_data_default.json',
    'bok_choy_data_student_module_history.json',
    'bok_choy_migrations_data_default.sql',
    'bok_choy_migrations_data_student_module_history.sql',
    'bok_choy_schema_default.sql',
    'bok_choy_schema_student_module_history.sql',
    'bok_choy_default_migrations.yaml',
    'bok_choy_student_module_history_migrations.yaml'
]


def _authenticate_with_github(github_token):
    """
    Authenticate with Github using a token.
    Returns a github instance.
    """
    try:
        github_instance = Github(github_token)
    except:
        raise StandardError(
            "Failed connecting to Github. " +
            "Please make sure the credentials are accurate and try again."
        )
    return github_instance


def _connect_to_repo(github_instance, repo_name):
    """
    Get the repository object of the desired repo.
    Returns the repository object.
    """
    repos_list = github_instance.get_user().get_repos()
    repository = None
    for repo in repos_list:
        if repo.name == repo_name:
            repository = repo
            break
    if not repository:
        raise StandardError(
            "Could not connect to the repository: {}. "
            "Please make sure you are using the correct "
            "credentials and try again.".format(repo_name)
        )
    return repository


def _get_file_sha(repository, file_path):
    """
    Finds the sha of a specific file in the repository.
    Returns the file sha.
    """
    try:
        # Get the blob sha of the db file on our branch
        file_sha = repository.get_file_contents(file_path).sha
    except:
        raise StandardError(
            "Could not locate file: {}".format(file_path)
        )
    return file_sha


def _read_file_contents(file_path):
    """
    Read the contents of a file and return a string of the data.
    Returns a string of the file contents.
    """
    try:
        with open(file_path, 'r') as opened_file:
            data = opened_file.read()
    except:
        raise StandardError(
            "Unable to read file: {}".format(file_path)
        )
    return data


def _file_has_changed(repository, local_file, file_path):
    """
    Checks to see if a file differs from the current version
    in a repo.
    Returns true if the files are different.
    """
    try:
        repo_file_contents = repository.get_file_contents(file_path).decoded_content
    except:
        raise StandardError(
            "Could not get contents of file: {}".format(file_path)
        )
    return local_file != repo_file_contents


def _create_branch(repository, branch_name, sha):
    """
    Create a new branch with the given sha as its head.
    """
    try:
        repository.create_git_ref(branch_name, sha)
    except:
        raise StandardError(
            "Unable to create git branch: {}. "
            "Check to make sure this branch doesn't already exist.".format(branch_name)
        )


def _update_file(repository, file_path, commit_message, contents, file_sha, branch_name):
    """
    Create a commit on a branch that updates the file_path with the string contents.
    """
    try:
        repository.update_file(file_path, commit_message, contents, file_sha, branch_name)
    except:
        raise StandardError(
            "Error updating database file: {}".format(file_path)
        )


def _create_pull_request(repository, title, body, base, head):
    """
    Create a new pull request with the changes in head.
    """
    try:
        pull_request = repository.create_pull(
            title=title,
            body=body,
            base=base,
            head=head
        )
    except:
        raise StandardError(
            "Could not create pull request"
        )


@click.command()
@click.option(
    '--sha',
    help="Sha of the merge commit to base the new PR off of",
    required=True,
)
@click.option(
    '--github_token',
    help="Github token for authentication",
    required=True,
)
@click.option(
    '--repo_root',
    help="Path to local edx-platform repository that will "
         "hold updated database files",
    required=True,
)
def main(sha, github_token, repo_root):
    # Connect to github
    logger.info("Authenticating with Github")
    github_instance = _authenticate_with_github(github_token)
    repository = _connect_to_repo(github_instance, "edx-platform")

    # Iterate through the db files and update them accordingly
    branch_created = False
    for db_file in BOKCHOY_DB_FILES:
        repo_file_path = os.path.join('/', DB_CACHE_FILEPATH, db_file)

        # Get the sha of the file in the repository
        file_sha = _get_file_sha(repository, repo_file_path)

        # Read the local db files that were updated by paver
        local_file_path = os.path.join(repo_root, DB_CACHE_FILEPATH, db_file)
        local_file_data = _read_file_contents(local_file_path)

        # Check if the local file is different from whats in the repo currently
        if _file_has_changed(repository, local_file_data, repo_file_path):
            logger.info("File {} has changed.".format(repo_file_path))
            # Since there are changes needed, create a new branch if we haven't already
            if not branch_created:
                # Create a new branch for the db file changes
                branch_name = "refs/heads/bokchoy_auto_cache_update_" + sha
                _create_branch(repository, branch_name, sha)
                branch_created = True

            # Update the db files on our branch to reflect the new changes
            logger.info("Updating database file: {}".format(repo_file_path))
            _update_file(repository, repo_file_path, 'Updating migrations', local_file_data, file_sha, branch_name)

    # If there are changes, create a pull request against master and tag testeng for further action
    if branch_created:
        logger.info("Creating a new pull request.")
        _create_pull_request(
            repository,
            'Bokchoy db cache update',
            '@edx/testeng please review',
            'master',
            branch_name
        )
    else:
        logger.info("No changes needed.")


if __name__ == "__main__":
    main()
