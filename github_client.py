import logging
from typing import Dict, List, Optional

import requests


class GitHubClient:
    """Minimal GitHub API helper for fetching pull request data."""

    def __init__(self, token: str, repo: str, base_url: str = "https://api.github.com") -> None:
        self.repo = repo
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "code-review-agent/1.0",
            }
        )
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[Dict[str, str]] = None) -> requests.Response:
        url = f"{self.base_url}{path}"
        logging.debug("GET %s params=%s", url, params)
        response = self.session.get(url, params=params, timeout=30)
        if not response.ok:
            raise RuntimeError(f"GitHub API error {response.status_code}: {response.text}")
        return response

    def pull_request(self, number: int) -> Dict:
        path = f"/repos/{self.repo}/pulls/{number}"
        return self._get(path).json()

    def pull_request_files(self, number: int) -> List[Dict]:
        path = f"/repos/{self.repo}/pulls/{number}/files"
        files: List[Dict] = []
        page = 1
        while True:
            response = self._get(path, params={"per_page": 100, "page": page})
            chunk = response.json()
            files.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1
        return files

    def pull_request_diff(self, number: int) -> str:
        path = f"/repos/{self.repo}/pulls/{number}"
        headers = {"Accept": "application/vnd.github.v3.diff"}
        url = f"{self.base_url}{path}"
        logging.debug("GET %s (diff)", url)
        diff_response = self.session.get(url, headers=headers, timeout=30)
        if not diff_response.ok:
            raise RuntimeError(
                f"GitHub API diff error {diff_response.status_code}: {diff_response.text}"
            )
        return diff_response.text
