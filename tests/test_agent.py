from code_reviewer.agent import PullRequestAgent, parse_bitbucket_repo_slug


def test_parse_bitbucket_repo_slug_accepts_url_and_slug():
    assert parse_bitbucket_repo_slug("workspace/repo") == "workspace/repo"
    assert parse_bitbucket_repo_slug("https://bitbucket.org/workspace/repo") == "workspace/repo"
    assert parse_bitbucket_repo_slug("https://bitbucket.org/workspace/repo.git") == "workspace/repo"


def test_prompt_truncates_large_diff():
    agent = PullRequestAgent(
        bitbucket_repo="team/repo",
        bitbucket_username="user",
        bitbucket_token="token",
        gigachat_token="giga",
        max_diff_chars=10,
    )
    pr = {
        "id": 7,
        "title": "Update logic",
        "author": {"display_name": "Alice"},
        "links": {"html": {"href": "https://bitbucket.org/team/repo/pull-requests/7"}},
        "description": "Example change",
    }
    diff = "0123456789abcdefghij"

    prompt = agent._build_prompt(pr, diff)  # pylint: disable=protected-access

    assert "... truncated ..." in prompt
    assert "Diff:" in prompt
    assert "Pull Request: #7" in prompt
