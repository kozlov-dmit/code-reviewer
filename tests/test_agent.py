import re

import pytest

from agent import PullRequestAgent


def test_prompt_contains_pr_metadata_and_patch():
    agent = PullRequestAgent(
        github_repo="owner/repo",
        github_token="token",
        gigachat_token="giga",
        max_patch_chars=40,  # small to force truncation
    )

    pr = {
        "number": 42,
        "title": "Add new feature",
        "user": {"login": "alice"},
        "html_url": "https://github.com/owner/repo/pull/42",
        "body": "Implements a great feature.",
        "base": {"repo": {"full_name": "owner/repo"}},
    }

    files = [
        {
            "filename": "app.py",
            "status": "modified",
            "patch": "\n".join(
                [
                    "@@ -1,3 +1,5 @@",
                    " import os",
                    " import sys",
                    "+def foo():",
                    "+    return 1",
                    "+# extra lines to force truncation",
                    "+a",
                    "+b",
                    "+c",
                    "+d",
                ]
            ),
        }
    ]

    prompt = agent._build_prompt(pr, files)  # pylint: disable=protected-access

    assert "Pull Request: #42 Add new feature" in prompt
    assert "Author: alice" in prompt
    assert "app.py (modified)" in prompt
    assert "@@ -1,3 +1,5 @@" in prompt

    # Ensure truncation marker appears when patch exceeds max_patch_chars
    assert "... truncated ..." in prompt
