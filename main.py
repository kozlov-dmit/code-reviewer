import argparse
import logging
import os
import sys

from agent import PullRequestAgent, from_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send GitHub Pull Request to GigaChat for a quick code review."
    )
    parser.add_argument("--repo", help="GitHub repo in owner/name format. Overrides GITHUB_REPO.")
    parser.add_argument(
        "--github-token", help="GitHub token. Overrides GITHUB_TOKEN environment variable."
    )
    parser.add_argument(
        "--gigachat-token", help="GigaChat token. Overrides GIGACHAT_TOKEN environment variable."
    )
    parser.add_argument(
        "--gigachat-url",
        default=None,
        help="GigaChat API base url. Defaults to GIGACHAT_API_URL or public endpoint.",
    )
    parser.add_argument("--gigachat-model", default=None, help="GigaChat model name.")
    parser.add_argument("pr", type=int, help="Pull Request number to review.")
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
        review = agent.review_pull_request(args.pr)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to review PR: %s", exc)
        return 1

    print("=== GigaChat review ===")
    print(review)
    return 0


if __name__ == "__main__":
    sys.exit(main())


def _agent_from_args(args: argparse.Namespace) -> PullRequestAgent:
    repo = args.repo or os.environ.get("GITHUB_REPO")
    github_token = args.github_token or os.environ.get("GITHUB_TOKEN")
    gigachat_token = args.gigachat_token or os.environ.get("GIGACHAT_TOKEN")
    gigachat_url = args.gigachat_url or os.environ.get(
        "GIGACHAT_API_URL", "https://gigachat.devices.sberbank.ru/api/v1"
    )
    gigachat_model = args.gigachat_model or os.environ.get("GIGACHAT_MODEL", "GigaChat")

    if repo and github_token and gigachat_token:
        return PullRequestAgent(
            github_repo=repo,
            github_token=github_token,
            gigachat_token=gigachat_token,
            gigachat_url=gigachat_url,
            gigachat_model=gigachat_model,
        )

    logging.debug("Falling back to environment for configuration")
    return from_env()
