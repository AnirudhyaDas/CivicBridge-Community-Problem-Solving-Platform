def calculate_final_score(
    impact: int,
    feasibility: int,
    cost_efficiency: int,
    credibility: int
):
    return (
        impact * 0.4 +
        feasibility * 0.3 +
        cost_efficiency * 0.2 +
        credibility * 0.1
    )
