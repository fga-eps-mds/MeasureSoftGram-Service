"""Métricas do SonarQube que o Service guarda por arquivo (qualifier = FIL)."""

FILE_LEVEL_METRICS = frozenset(
    {
        "coverage",
        "complexity",
        "functions",
        "comment_lines_density",
        "duplicated_lines_density",
        "sqale_debt_ratio",
    }
)
