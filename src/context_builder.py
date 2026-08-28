SYSTEM_INSTRUCTION = """
You are a Shopping AI Assistant.

Answer the user's question using only the retrieved context.

Rules:
- Do not invent products, prices, policies, or product attributes.
- If the context does not contain enough information, say that you do not have enough information.
- Respect product constraints from the user's query.
- Prefer factual answers grounded in the retrieved context.
- Reproduce discrete product attributes exactly as provided in the retrieved context.
- Do not convert discrete lists such as sizes or colors into ranges and do not infer missing intermediate values.
- For example, if sizes are XS, S, M, XL, keep XS, S, M, XL; never rewrite them as XS-XL because that would imply size L is available.
""".strip()


PROMPT_VERSION = "shopping-assistant-v3-cost-optimized"


def build_retrieved_context(results):
    blocks = []
    for result in results:
        blocks.append(
            f"""
Rank: {result['rank']}
ID: {result['id']}
Type: {result['type']}
Similarity Score: {result['score']:.4f}

{result['text']}
""".strip()
        )
    return "\n\n---\n\n".join(blocks)


def build_context(query, results):
    context_text = build_retrieved_context(results)
    return f"""
USER QUERY:
{query}

RETRIEVED CONTEXT:
{context_text}
""".strip()
