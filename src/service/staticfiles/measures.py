# flake8: noqa
GITHUB_AVAILABLE_METRICS = {
    "metrics": [
        {
            "id": "8000",
            "key": "resolved_issues_throughput",
            "type": "PERCENT",
            "name": "Resolved Issues’ Throughput",
            "description": "Density of issues whose resolution didn't take longer than the defined duration threshold.",
            "domain": "Productivity",
            "direction": 0,
            "qualitative": False,
            "hidden": False
        },
        {
            "id": "8002",
            "key": "issue_type_timeframe",
            "type": "PERCENT",
            "name": "Issues-type in a timeframe",
            "description": "Density of issues of a specific type within a defined timeframe.",
            "domain": "Productivity",
            "direction": 0,
            "qualitative": False,
            "hidden": False
        },
        {
            "id": "8001",
            "key": "team_throughput",
            "type": "PERCENT",
            "name": "Team Throughput",
            "description": "Density of issues resolved by a team in a given timeframe",
            "domain": "Productivity",
            "direction": 0,
            "qualitative": False,
            "hidden": False
        },
    ],
    "total": 3,
    "p": 8000,
    "ps": 2
}