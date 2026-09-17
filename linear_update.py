"""Update a Linear issue after merge; requires LINEAR_API_KEY."""

import argparse
import os

import httpx

API_URL = "https://api.linear.app/graphql"


def graphql(query: str, variables: dict) -> dict:
    response = httpx.post(
        API_URL,
        json={"query": query, "variables": variables},
        headers={"Authorization": os.environ["LINEAR_API_KEY"]},
        timeout=20,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def set_done(issue_identifier: str, state_name: str = "Done") -> None:
    issue = graphql(
        "query($id:String!){issue(id:$id){id team{states{nodes{id name}}}}}",
        {"id": issue_identifier},
    )["issue"]
    target = next((item for item in issue["team"]["states"]["nodes"] if item["name"] == state_name), None)
    if not target:
        raise RuntimeError(f"Linear workflow has no {state_name!r} state")
    graphql(
        "mutation($id:String!,$stateId:String!){issueUpdate(id:$id,input:{stateId:$stateId}){success}}",
        {"id": issue["id"], "stateId": target["id"]},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("issue", help="e.g. LIT-12")
    parser.add_argument("--state", default="Done")
    args = parser.parse_args()
    set_done(args.issue, args.state)
