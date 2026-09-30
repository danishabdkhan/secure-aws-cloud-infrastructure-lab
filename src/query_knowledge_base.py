import os

import boto3
from botocore.exceptions import ClientError

REGION = os.getenv("AWS_REGION", "us-east-1")
KNOWLEDGE_BASE_ID = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID")

if not KNOWLEDGE_BASE_ID:
    raise ValueError(
        "BEDROCK_KNOWLEDGE_BASE_ID environment variable is not set."
    )

client = boto3.client("bedrock-agent-runtime", region_name=REGION)


def get_source_name(result):
    metadata = result.get("metadata", {})

    document_title = metadata.get("_document_title")

    if document_title:
        return document_title

    return "Unknown source"


def ask_project_assistant(query):
    try:
        response = client.agentic_retrieve_stream(
            messages=[
                {
                    "role": "user",
                    "content": {"text": query}
                }
            ],
            retrievers=[
                {
                    "configuration": {
                        "knowledgeBase": {
                            "knowledgeBaseId": KNOWLEDGE_BASE_ID
                        }
                    }
                }
            ],
            agenticRetrieveConfiguration={
                "foundationModelType": "MANAGED",
                "maxAgentIteration": 5
            },
            generateResponse=True,
        )

        print("\nAnswer:\n")

        cited_sources = []

        for event in response["stream"]:
            if "responseEvent" in event:
                print(
                    event["responseEvent"].get("text", ""),
                    end="",
                    flush=True
                )

            elif "result" in event:
                result_event = event["result"]

                results = result_event.get("results", [])

                generated_response = result_event.get(
                    "generatedResponse", {}
                )

                for citation in generated_response.get("citations", []):
                    for reference in citation.get("references", []):
                        index = reference.get("resultIndex")

                        if (
                            index is not None
                            and 0 <= index < len(results)
                        ):
                            source = get_source_name(results[index])

                            if source not in cited_sources:
                                cited_sources.append(source)

        print("\n")

        if cited_sources:
            print("Sources:")
            for source in cited_sources:
                print(f"- {source}")

    except ClientError as error:
        print(f"\nAWS error: {error}")


if __name__ == "__main__":
    try:
        query = input("Ask a question about the AWS project: ").strip()

        if not query:
            print("Please enter a question.")
        else:
            ask_project_assistant(query)

    except KeyboardInterrupt:
        print("\nExiting.")