import boto3

REGION = "us-east-1"
KNOWLEDGE_BASE_ID = "QTIMYKAPIY"

client = boto3.client("bedrock-agent-runtime", region_name=REGION)

query = input("Ask a question about the AWS project: ")

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
    generateResponse=True
)

print("\nAnswer:\n")

for event in response["stream"]:
    if "responseEvent" in event:
        print(
            event["responseEvent"].get("text", ""),
            end="",
            flush=True
        )

    elif "result" in event:
        results = event["result"].get("results", [])

        if results:
            print("\n\nRetrieved sources:")
            for i, item in enumerate(results, start=1):
                content = item.get("content", {}).get("text", "")
                print(f"\n[{i}] {content}")

    elif "traceEvent" in event:
        attrs = event["traceEvent"].get("attributes", {})
        step = attrs.get("step")
        status = attrs.get("status")
        message = attrs.get("message")

        if message:
            print(f"\n[{step}/{status}] {message}")
