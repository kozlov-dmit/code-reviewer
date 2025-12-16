import argparse
import logging
import os
import sys

from .agent import PullRequestAgent, from_env, parse_bitbucket_repo_slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send all open Bitbucket Pull Requests to GigaChat for a quick code review."
    )
    # CLI flags mirror env vars so the agent can run locally or in CI.
    parser.add_argument("--repo-url", help="Bitbucket repo URL or <workspace>/<repo> slug.")
    parser.add_argument("--bitbucket-username", help="Bitbucket username (for app password auth).")
    parser.add_argument("--bitbucket-token", help="Bitbucket app password.")
    parser.add_argument(
        "--bitbucket-api-url",
        default=None,
        help="Bitbucket API base url. Defaults to BITBUCKET_API_URL or cloud endpoint.",
    )
    parser.add_argument("--gigachat-token", help="GigaChat token. Overrides GIGACHAT_TOKEN.")
    parser.add_argument(
        "--gigachat-url",
        default=None,
        help="GigaChat API base url. Defaults to GIGACHAT_API_URL or public endpoint.",
    )
    parser.add_argument("--gigachat-model", default=None, help="GigaChat model name.")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging for troubleshooting."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        agent = _agent_from_args(args)
    except ValueError as exc:
        logging.error(exc)
        return 1

    try:
        results = agent.review_open_pull_requests()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to review open PRs: %s", exc)
        return 1

    if not results:
        print("No open pull requests.")
        return 0

    for pr in results:
        print(f"[PR #{pr['id']}] {pr['title']}")
        if pr.get("url"):
            print(pr["url"])
        print(pr["review"])
        print("-" * 40)
    return 0


if __name__ == "__main__":
    sys.exit(main())


def _agent_from_args(args: argparse.Namespace) -> PullRequestAgent:
    repo_url = (
        args.repo_url or os.environ.get("BITBUCKET_REPO") or os.environ.get("BITBUCKET_REPO_URL")
    )
    bitbucket_username = args.bitbucket_username or os.environ.get("BITBUCKET_USERNAME")
    bitbucket_token = args.bitbucket_token or os.environ.get("BITBUCKET_TOKEN")
    gigachat_token = args.gigachat_token or os.environ.get("GIGACHAT_TOKEN")
    bitbucket_api_url = args.bitbucket_api_url or os.environ.get(
        "BITBUCKET_API_URL", "https://api.bitbucket.org/2.0"
    )
    gigachat_url = args.gigachat_url or os.environ.get(
        "GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1"
    )
    gigachat_model = args.gigachat_model or os.environ.get("GIGACHAT_MODEL", "GigaChat")

    if repo_url and bitbucket_username and bitbucket_token and gigachat_token:
        repo_slug = parse_bitbucket_repo_slug(repo_url)
        return PullRequestAgent(
            bitbucket_repo=repo_slug,
            bitbucket_username=bitbucket_username,
            bitbucket_token=bitbucket_token,
            gigachat_token=gigachat_token,
            bitbucket_api_url=bitbucket_api_url,
            gigachat_url=gigachat_url,
            gigachat_model=gigachat_model,
        )

    logging.debug("Falling back to environment for configuration")
    return from_env()
