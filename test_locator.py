from utils.source_locator import SourceLocator


repository_path = (
    "data/repositories/Simple-RAG-Chatbot"
)

locator = SourceLocator(
    repository_path
)


results = locator.find_term(
    "src/RAG_ChatBot.py",
    "PineconeVectorStore.from_documents"
)


print("\n" + "=" * 70)
print("SOURCE LOCATOR")
print("=" * 70)


for result in results:

    print(
        f"{result['file_path']}:"
        f"{result['line']}"
    )

    print(
        result["content"]
    )