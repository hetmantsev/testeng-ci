from unittest import TestCase

import click
from click.testing import CliRunner
from mock import patch, Mock

from jenkins.bokchoy_db_pull_request import (_authenticate_with_github, _connect_to_repo,
                                             _get_file_sha, _read_file_contents, _file_has_changed,
                                             _create_branch, _update_file, _create_pull_request,
                                             main)


class BokchoyPullRequestTestCase(TestCase):
    """
    Test Case class for bokchoy_db_pull_request.py.
    """

    # Create the Cli runner to run the main function with click arguments
    runner = CliRunner()

    @patch('jenkins.bokchoy_db_pull_request._authenticate_with_github',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._connect_to_repo',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._get_file_sha',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._read_file_contents',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._file_has_changed',
           return_value=False)
    @patch('jenkins.bokchoy_db_pull_request._create_branch',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._update_file',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._create_pull_request',
           return_value=None)
    def test_no_changes(
        self, create_pr_mock, update_file_mock, create_branch_mock, file_changed_mock, read_file_mock,
        file_sha_mock, repo_mock, github_mock
    ):
        """
        Ensure a merge with no changes to db files will not result in any updates.
        """
        result = self.runner.invoke(main, args=['--sha=123', '--github_token=1234', '--repo_root=../../repo'])
        assert not create_branch_mock.called
        assert not update_file_mock.called
        assert not create_pr_mock.called

    @patch('jenkins.bokchoy_db_pull_request._authenticate_with_github',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._connect_to_repo',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._get_file_sha',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._read_file_contents',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._file_has_changed',
           return_value=True)
    @patch('jenkins.bokchoy_db_pull_request._create_branch',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._update_file',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._create_pull_request',
           return_value=None)
    def test_changes(
        self, create_pr_mock, update_file_mock, create_branch_mock, file_changed_mock, read_file_mock,
        file_sha_mock, repo_mock, github_mock
    ):
        """
        Ensure a merge with changes to db files will result in the proper updates, a new branch, and a PR.
        """
        result = self.runner.invoke(main, args=['--sha=123', '--github_token=1234', '--repo_root=../../repo'])
        assert create_branch_mock.called
        self.assertEqual(create_branch_mock.call_count, 1)
        assert update_file_mock.called
        assert create_pr_mock.called

    @patch('jenkins.bokchoy_db_pull_request._authenticate_with_github',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._connect_to_repo',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._get_file_sha',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._read_file_contents',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._file_has_changed',
           side_effect=[True, False, False, False, False, False, False, False])
    @patch('jenkins.bokchoy_db_pull_request._create_branch',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._update_file',
           return_value=None)
    @patch('jenkins.bokchoy_db_pull_request._create_pull_request',
           return_value=None)
    def test_one_change(
        self, create_pr_mock, update_file_mock, create_branch_mock, file_changed_mock, read_file_mock,
        file_sha_mock, repo_mock, github_mock
    ):
        """
        Ensure a merge with changes to one file will result in updating only that file, as well as a new branch and PR.
        """
        result = self.runner.invoke(main, args=['--sha=123', '--github_token=1234', '--repo_root=../../repo'])
        assert create_branch_mock.called
        self.assertEqual(create_branch_mock.call_count, 1)
        assert update_file_mock.called
        self.assertEqual(update_file_mock.call_count, 1)
        assert create_pr_mock.called
