import pandas as pd
from collections import Counter


def build_explainability_summary(
    persona_name,
    conditions,
    allergies,
    diet,
    notes,
    exclusion_log
):
    summary_lines = []

    summary_lines.append(
        f"{persona_name}'s plan was personalized using:"
    )

    if conditions:
        summary_lines.append(
            f"• Clinical conditions: {', '.join(conditions)}"
        )

    if allergies:
        summary_lines.append(
            f"• Allergies/intolerances: {', '.join(allergies)}"
        )

    summary_lines.append(
        f"• Diet preference: {diet}"
    )

    if notes.strip():
        summary_lines.append(
            f"• Optional constraints: {notes}"
        )

    summary_lines.append("")
    summary_lines.append("Meals were excluded because:")

    reason_counts = Counter()

    for row in exclusion_log:

        reason = row["reason"]

        if "Hypertension" in reason:
            reason_counts["Exceeded Hypertension sodium threshold"] += 1

        elif "Type 2 Diabetes" in reason:
            reason_counts["Exceeded Diabetes GI threshold"] += 1

        elif "vegetarian diet" in reason.lower():
            reason_counts["Not compatible with Vegetarian diet"] += 1

        elif "vegan diet" in reason.lower():
            reason_counts["Not compatible with Vegan diet"] += 1

        elif "pescatarian diet" in reason.lower():
            reason_counts["Not compatible with Pescatarian diet"] += 1

        elif "gluten" in reason.lower():
            reason_counts["Contained gluten"] += 1

        elif "dairy" in reason.lower():
            reason_counts["Contained dairy"] += 1

        elif "soy" in reason.lower():
            reason_counts["Contained soy"] += 1

        elif "tree nuts" in reason.lower():
            reason_counts["Contained tree nuts"] += 1

        elif "shellfish" in reason.lower():
            reason_counts["Contained shellfish"] += 1

        elif "IBS" in reason:
            reason_counts["Contained high-FODMAP ingredients"] += 1

        elif "GERD" in reason:
            reason_counts["Contained GERD trigger ingredients"] += 1

        else:
            reason_counts["Other filtering reason"] += 1

    if reason_counts:
        for reason, count in sorted(
            reason_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            summary_lines.append(
                f"• {count} meals: {reason}"
            )
    else:
        summary_lines.append(
            "• No meals needed exclusion."
        )

    return "\n".join(summary_lines)


def convert_plan_to_csv(plan_df):
    return plan_df.to_csv(index=False).encode("utf-8")