import logging
from typing import Dict, List, Optional

import requests


class BitbucketClient:
    """Minimal Bitbucket API helper for pull requests."""

    def __init__(
        self,
        repo_slug: str,
        username: str,
        token: str,
        base_url: str = "https://api.bitbucket.org/2.0",
    ) -> None:
        if "/" not in repo_slug:
            raise ValueError("Bitbucket repo slug must look like <workspace>/<repo>")

        self.workspace, self.repo = repo_slug.split("/", 1)
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        # Bitbucket Cloud uses basic auth with username + app password.
        self.session.auth = (username, token)
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "code-review-agent/1.0",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        json=None,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        logging.debug("%s %s params=%s", method, url, params)
        response = self.session.request(
            method, url, params=params, headers=headers, json=json, timeout=60
        )
        if not response.ok:
            raise RuntimeError(f"Bitbucket API error {response.status_code}: {response.text}")
        return response

    def list_open_pull_requests(self) -> List[Dict]:
        """Return all open PRs with pagination."""
        path = f"/repositories/{self.workspace}/{self.repo}/pullrequests"
        params: Dict[str, str] = {"state": "OPEN", "pagelen": "50"}
        results: List[Dict] = []

        next_path: Optional[str] = path
        while next_path:
            response = self._request("GET", next_path, params=params)
            data = response.json()
            results.extend(data.get("values", []))

            next_url = data.get("next")
            if not next_url:
                break
            # The `next` link already contains query params; reuse it as-is.
            next_path = next_url.replace(self.base_url, "")
            params = {}  # pagination URL already has query params
        return results

    def pull_request(self, pr_id: int) -> Dict:
        path = f"/repositories/{self.workspace}/{self.repo}/pullrequests/{pr_id}"
        return self._request("GET", path).json()

    def pull_request_diff(self, pr_id: int) -> str:
        path = f"/repositories/{self.workspace}/{self.repo}/pullrequests/{pr_id}/diff"
        headers = {"Accept": "text/plain"}
        return self._request("GET", path, headers=headers).text

    def comment_pull_request(self, pr_id: int, text: str) -> Dict:
        path = f"/repositories/{self.workspace}/{self.repo}/pullrequests/{pr_id}/comments"
        payload = {"content": {"raw": text}}
        return self._request("POST", path, json=payload).json()
