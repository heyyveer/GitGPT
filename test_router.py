from agents.router import QueryRouter


router = QueryRouter()


questions = [
    "Where is the Pinecone vector store initialized?",
    "How do I install this project?",
    "Why does the application fail when connecting to Pinecone?",
    "How does the RAG pipeline work in this repository?",
    "What dependencies does this project use?"
]


for question in questions:

    category = router.route(question)

    print("\n" + "=" * 70)

    print("Question:", question)

    print("Route:", category)