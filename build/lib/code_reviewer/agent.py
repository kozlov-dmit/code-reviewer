import logging
import os
from typing import Dict, List
from urllib.parse import urlparse

from .bitbucket_client import BitbucketClient
from .gigachat_client import GigaChatClient


def parse_bitbucket_repo_slug(value: str) -> str:
    """Return <workspace>/<repo> from either slug or full Bitbucket URL."""
    if not value:
        raise ValueError("Bitbucket repo URL/slug is required")

    trimmed = value.strip()
    slug = trimmed
    if "://" in trimmed:
        # Accept full clone URLs and extract only the workspace/repo part.
        parsed = urlparse(trimmed)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 2:
            raise ValueError("Bitbucket repo URL must contain workspace and repo segments")
        slug = "/".join(parts[:2])

    if slug.endswith(".git"):
        slug = slug[:-4]
    if "/" not in slug:
        raise ValueError("Bitbucket repo slug must look like <workspace>/<repo>")
    return slug


class PullRequestAgent:
    """Coordinates PR loading from Bitbucket and review request to GigaChat."""

    def __init__(
        self,
        bitbucket_repo: str,
        bitbucket_username: str,
        bitbucket_token: str,
        gigachat_token: str,
        bitbucket_api_url: str = "https://api.bitbucket.org/2.0",
        gigachat_url: str = "https://gigachat.devices.sberbank.ru/api/v1",
        gigachat_model: str = "GigaChat",
        max_diff_chars: int = 12000,
    ) -> None:
        repo_slug = parse_bitbucket_repo_slug(bitbucket_repo)
        self.bitbucket = BitbucketClient(
            repo_slug=repo_slug,
            username=bitbucket_username,
            token=bitbucket_token,
            base_url=bitbucket_api_url,
        )
        self.gigachat = GigaChatClient(
            token=gigachat_token,
            base_url=gigachat_url,
            model=gigachat_model,
        )
        self.max_diff_chars = max_diff_chars
        self.repo_slug = repo_slug

    def review_open_pull_requests(self) -> List[Dict[str, str]]:
        prs = self.bitbucket.list_open_pull_requests()
        if not prs:
            logging.info("No open pull requests in %s", self.repo_slug)
            return []

        results: List[Dict[str, str]] = []
        for pr in prs:
            pr_id = pr.get("id")
            if pr_id is None:
                logging.warning("Skip PR without id: %s", pr)
                continue
            try:
                # Fetch diff -> ask GigaChat -> post comment for each PR.
                diff = self.bitbucket.pull_request_diff(pr_id)
                prompt = self._build_prompt(pr, diff)
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "Act as a senior backend engineer. Provide concise, actionable code review."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ]
                logging.info("Sending PR #%s to GigaChat for review", pr_id)
                review = self.gigachat.chat(messages)
                self.bitbucket.comment_pull_request(pr_id, review)
                results.append(
                    {
                        "id": pr_id,
                        "title": pr.get("title", ""),
                        "url": pr.get("links", {}).get("html", {}).get("href", ""),
                        "review": review,
                    }
                )
                logging.info("Posted review comment to PR #%s", pr_id)
            except Exception as exc:  # pylint: disable=broad-except
                logging.error("Failed to review PR %s: %s", pr_id, exc)
        return results

    def _build_prompt(self, pr: Dict, diff: str) -> str:
        author = pr.get("author", {}) or {}
        author_name = author.get("display_name") or author.get("nickname") or "unknown"
        header = (
            f"Repository: {self.repo_slug}\n"
            f"Pull Request: #{pr.get('id')} {pr.get('title')}\n"
            f"Author: {author_name}\n"
            f"URL: {pr.get('links', {}).get('html', {}).get('href', '')}\n"
            f"Description:\n{pr.get('description') or 'No description provided.'}\n"
        )

        truncated_diff = diff
        if len(diff) > self.max_diff_chars:
            # Prevent oversized prompts to the model.
            truncated_diff = diff[: self.max_diff_chars] + "\n... truncated ..."

        instructions = (
            "Сделай краткий code review этого диффа. Сначала перечисли критичные проблемы, "
            "затем рекомендации и улучшения. Ответ держи сжато и на русском языке."
        )
        return header + "\nDiff:\n" + truncated_diff + "\n" + instructions


def from_env() -> PullRequestAgent:
    repo = os.environ.get("BITBUCKET_REPO") or os.environ.get("BITBUCKET_REPO_URL")
    username = os.environ.get("BITBUCKET_USERNAME")
    token = os.environ.get("BITBUCKET_TOKEN")
    gigachat_token = os.environ.get("GIGACHAT_TOKEN")
    bitbucket_api_url = os.environ.get("BITBUCKET_API_URL", "https://api.bitbucket.org/2.0")
    gigachat_url = os.environ.get("GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1")
    gigachat_model = os.environ.get("GIGACHAT_MODEL", "GigaChat")

    if not repo:
        raise ValueError("BITBUCKET_REPO or BITBUCKET_REPO_URL must be set")
    if not username:
        raise ValueError("BITBUCKET_USERNAME must be set")
    if not token:
        raise ValueError("BITBUCKET_TOKEN must be set")
    if not gigachat_token:
        raise ValueError("GIGACHAT_TOKEN must be set")

    return PullRequestAgent(
        bitbucket_repo=repo,
        bitbucket_username=username,
        bitbucket_token=token,
        gigachat_token=gigachat_token,
        bitbucket_api_url=bitbucket_api_url,
        gigachat_url=gigachat_url,
        gigachat_model=gigachat_model,
    )
