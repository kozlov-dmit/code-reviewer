import logging
import os
from typing import Dict, List

from gigachat_client import GigaChatClient
from github_client import GitHubClient


class PullRequestAgent:
    """Coordinates PR loading from GitHub and review request to GigaChat."""

    def __init__(
        self,
        github_repo: str,
        github_token: str,
        gigachat_token: str,
        gigachat_url: str = "https://gigachat.devices.sberbank.ru/api/v1",
        gigachat_model: str = "GigaChat",
        max_patch_chars: int = 12000,
    ) -> None:
        self.github = GitHubClient(token=github_token, repo=github_repo)
        self.gigachat = GigaChatClient(
            token=gigachat_token, base_url=gigachat_url, model=gigachat_model
        )
        self.max_patch_chars = max_patch_chars

    def review_pull_request(self, pr_number: int) -> str:
        pr = self.github.pull_request(pr_number)
        files = self.github.pull_request_files(pr_number)
        prompt = self._build_prompt(pr, files)
        messages = [
            {
                "role": "system",
                "content": "Act as a senior backend engineer. Provide concise, actionable code review.",
            },
            {"role": "user", "content": prompt},
        ]
        logging.info("Sending PR #%s to GigaChat for review", pr_number)
        return self.gigachat.chat(messages)

    def _build_prompt(self, pr: Dict, files: List[Dict]) -> str:
        header = (
            f"Repository: {pr['base']['repo']['full_name']}\n"
            f"Pull Request: #{pr['number']} {pr['title']}\n"
            f"Author: {pr['user']['login']}\n"
            f"URL: {pr['html_url']}\n"
            f"Description:\n{pr.get('body') or 'No description provided.'}\n"
        )

        file_sections: List[str] = []
        used_chars = 0
        for file in files:
            patch = file.get("patch") or ""
            if not patch:
                continue
            truncated_patch = patch
            remaining = self.max_patch_chars - used_chars
            if remaining <= 0:
                break
            if len(patch) > remaining:
                truncated_patch = patch[:remaining]
                truncated_patch += "\n... truncated ..."
            used_chars += len(truncated_patch)
            section = (
                f"\nFile: {file['filename']} ({file['status']})\n"
                f"Patch:\n{truncated_patch}\n"
            )
            file_sections.append(section)

        instructions = (
            "Review the pull request. Highlight critical issues first, then suggestions. "
            "Return a short summary in Russian."
        )
        return header + "\n".join(file_sections) + "\n" + instructions


def from_env() -> PullRequestAgent:
    github_repo = os.environ.get("GITHUB_REPO")
    github_token = os.environ.get("GITHUB_TOKEN")
    gigachat_token = os.environ.get("GIGACHAT_TOKEN")
    gigachat_url = os.environ.get("GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1")
    gigachat_model = os.environ.get("GIGACHAT_MODEL", "GigaChat")

    if not github_repo:
        raise ValueError("GITHUB_REPO must be set (format: owner/name)")
    if not github_token:
        raise ValueError("GITHUB_TOKEN must be set")
    if not gigachat_token:
        raise ValueError("GIGACHAT_TOKEN must be set")

    return PullRequestAgent(
        github_repo=github_repo,
        github_token=github_token,
        gigachat_token=gigachat_token,
        gigachat_url=gigachat_url,
        gigachat_model=gigachat_model,
    )
