from dotenv import load_dotenv

load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from drug_reference import DRUG_REFERENCE


# Score cutoff for filtering out weakly relevant chunks
SCORE_CUTOFF = 0.35

CHROMA_PATH = "chroma"

# Prompt templates for RAG pipeline
PROMPT_TEMPLATE = """
You are an evidence-based diabetes information assistant.

Answer the user's question using only the supplied context.

Rules:
- Use only facts supported by the supplied context.
- You may combine information from multiple supplied passages.
- Do not use outside knowledge.
- Do not invent missing details.
- Do not force loosely related context to answer the question.
- If the supplied context does not contain enough relevant information,
  respond exactly:
  "I cannot answer that question from the diabetes guidelines in my database."

When answering:
- Be clear and concise.
- Include important units, thresholds, or qualifications when available.
- Do not claim that something is recommended unless the context supports it.

Context:

{context}

---

Question: {question}
"""

SCOPE_TEMPLATE = """
Determine whether the user's question is related to diabetes or information
that could reasonably be answered by a diabetes evidence database.

IN_SCOPE includes questions about:
- Diabetes and prediabetes
- Type 1, type 2, and gestational diabetes
- Blood glucose, fasting glucose, glucose tolerance tests, and A1C
- Diagnosis and diagnostic thresholds
- Diabetes prevalence, statistics, epidemiology, and risk factors
- Screening, prevention, treatment, and management
- Insulin and other diabetes medications
- Nutrition, exercise, weight management, and lifestyle guidance
- Diabetes complications and associated health conditions
- Recommendations contained in diabetes guidelines

OUT_OF_SCOPE includes questions clearly unrelated to diabetes, such as:
- Broken bones or unrelated injuries
- Unrelated infections or diseases
- General technology, entertainment, travel, or other nonmedical topics

Classify borderline or potentially diabetes-related questions as IN_SCOPE.
Return only one of these exact values:

IN_SCOPE
OUT_OF_SCOPE

Question: {question}
"""

CONDENSE_TEMPLATE = """
Given the conversation history and a follow-up question, rewrite the
follow-up question as a standalone question that includes any necessary
context from the history. If the follow-up question is already standalone,
return it unchanged.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:
"""


def retrieve_chunks(
    db,
    query,
    k=6,
    fetch_k=25,
    lambda_mult=0.5,
    score_cutoff=None,
):
    """
    Retrieve relevant and diverse chunks.

    MMR helps avoid returning several near-duplicate excerpts from the
    same section.
    """
    # Retrieve scored candidates to check the best score against the cutoff
    scored_candidates = db.similarity_search_with_score(
        query,
        k=fetch_k,
    )

    if not scored_candidates:
        return []

    best_score = scored_candidates[0][1]

    # Reject retrieval if even the closest match is too weak
    if score_cutoff is not None and best_score > score_cutoff:
        return []

    return db.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
    )


def extract_drugs_mentioned(context_text: str):
    """
    Extract drug names mentioned in the supplied text using DRUG_REFERENCE.
    Returns a list of matching drug names and classes.
    """
    mentioned = []
    lower_context = context_text.lower()

    # Check for each drug in the reference dictionary if it is mentioned in the context
    for drug, drug_class in DRUG_REFERENCE.items():
        if drug.lower() in lower_context:
            mentioned.append({
                "drug": drug,
                "class": drug_class,
            })

    return mentioned


def condense_question(model, chat_history, question):
    """
    Condense a follow-up question into a standalone question using
    conversation history.
    """
    if not chat_history:
        return question

    history_text = "\n".join(
        f"{turn['role'].capitalize()}: {turn['content']}"
        for turn in chat_history
    )

    # Create a prompt to condense the question
    prompt = ChatPromptTemplate.from_template(
        CONDENSE_TEMPLATE
    ).format(
        chat_history=history_text,
        question=question,
    )

    response = model.invoke(prompt)

    return response.content.strip()


def group_sources(documents):
    """
    Group retrieved chunks from the same source and combine
    their page numbers into one list.
    """
    grouped = {}
    order = []

    for doc in documents:
        key = (
            doc.metadata.get("source_url")
            or doc.metadata.get("source")
            or doc.metadata.get("title")
        )

        # If the source is not already in the grouped dictionary, add it with its metadata
        if key not in grouped:
            grouped[key] = {
                "title": doc.metadata.get(
                    "title",
                    "Unknown source",
                ),
                "citation": doc.metadata.get(
                    "citation",
                    "Citation unavailable",
                ),
                "source_url": doc.metadata.get("source_url"),
                "pages": set(),
            }

            order.append(key)

        page = doc.metadata.get("page")

        if page is not None:
            grouped[key]["pages"].add(page + 1)

    sources = []

    for key in order:
        source = grouped[key]
        source["pages"] = sorted(source["pages"])
        sources.append(source)

    return sources


def query_rag(
    query_text: str,
    chat_history=None,
    k: int = 8,
):
    """
    Answer a diabetes-related question using retrieved guideline chunks.

    Returns:
        answer: str
        sources: list[dict]
        drugs_mentioned: list[dict]
    """
    query_text = query_text.strip()
    chat_history = chat_history or []

    if not query_text:
        return "Please enter a diabetes-related question.", [], []

    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
    )

    # Rewrite follow-up questions as standalone questions
    standalone_question = condense_question(
        model,
        chat_history,
        query_text,
    )

    # Reject clearly out-of-scope questions
    scope_prompt = ChatPromptTemplate.from_template(
        SCOPE_TEMPLATE
    ).format(
        question=standalone_question
    )

    scope_response = model.invoke(scope_prompt)
    scope_result = scope_response.content.strip().upper()

    if scope_result != "IN_SCOPE":
        return (
            "I can only answer questions covered by the diabetes "
            "guidelines in my database.",
            [],
            [],
        )

    # Load Chroma database
    embedding_function = OpenAIEmbeddings()

    db = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embedding_function,
    )

    # Retrieve relevant chunks
    results = retrieve_chunks(
        db,
        standalone_question,
        k=6,
        fetch_k=25,
        score_cutoff=SCORE_CUTOFF,
    )

    if not results:
        return (
            "I cannot answer that question from the diabetes guidelines "
            "in my database.",
            [],
            [],
        )

    # Combine retrieved chunks into context
    context_text = "\n\n---\n\n".join(
        doc.page_content for doc in results
    )

    # Generate answer
    answer_prompt = ChatPromptTemplate.from_template(
        PROMPT_TEMPLATE
    ).format(
        context=context_text,
        question=standalone_question,
    )

    response = model.invoke(answer_prompt)
    answer = response.content.strip()

    # Extract medications mentioned in the final answer
    drugs_mentioned = extract_drugs_mentioned(answer)

    # Hide sources when context was insufficient
    if answer.startswith("I cannot answer"):
        return answer, [], []

    # Group duplicate sources
    sources = group_sources(results)

    return answer, sources, drugs_mentioned


if __name__ == "__main__":
    answer, sources, drugs_mentioned = query_rag(
        "What is the target A1C for most adults with type 2 diabetes?"
    )

    print("ANSWER:\n", answer)
    print("\nSOURCES:\n", sources)
    print("\nDRUGS MENTIONED:\n", drugs_mentioned)