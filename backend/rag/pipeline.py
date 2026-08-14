from rag.retriever import search_menu


def recommend(
    query: str,
    limit: int = 6,
    max_calories: float | None = None,
    min_protein: float | None = None,
    diet: str | None = None,
) -> dict:
    items = search_menu(query, limit, max_calories, min_protein, diet)
    if items:
        names = ", ".join(item["name"].title() for item in items[:3])
        message = f"I found {len(items)} grounded matches. Top picks: {names}."
    else:
        message = "No menu items matched those constraints. Try a broader food or cuisine."
    return {"query": query, "message": message, "results": items}
