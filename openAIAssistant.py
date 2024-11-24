
from openai import OpenAI
import csv
import json
import os
import time

# OpenAI API key

client = OpenAI()

# Paths
csv_path = "C:/Users/František/Downloads/time_series_covid19_confirmed_global.csv"
text_file_path = "C:/Users/František/Downloads/time_series_covid19_confirmed_global.txt"
json_file_path = "C:/Users/František/Downloads/time_series_covid19_confirmed_global.json"

# Check if CSV exists
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"File not found: {csv_path}")


# Convert CSV to plain text
def convert_csv_to_text(csv_path, text_file_path):
    with open(csv_path, "r", encoding="utf-8") as csv_file, open(text_file_path, "w", encoding="utf-8") as txt_file:
        reader = csv.reader(csv_file)
        headers = next(reader)  # Read the header row
        txt_file.write(", ".join(headers) + "\n")
        for row in reader:
            txt_file.write(", ".join(row) + "\n")
    print(f"CSV converted to text file at: {text_file_path}")


# Convert CSV to JSON
def convert_csv_to_json(csv_path, json_file_path):
    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        data = [row for row in reader]
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"CSV converted to JSON file at: {json_file_path}")


# Create and upload file to vector store
def upload_file_to_vector_store(file_path, mime_type, store_name="CovidInfoStore"):
    # Create a vector store
    vector_store = client.beta.vector_stores.create(name=store_name)
    print(f"Vector store created: {vector_store.id}")

    # Open the file and upload
    with open(file_path, "rb") as file_stream:
        filename = os.path.basename(file_path)
        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[(filename, file_stream, mime_type)],
        )
    print(f"File batch uploaded: {file_batch.status}")
    return vector_store.id


# Setup the assistant
def setup_assistant(vector_store_id):
    assistant = client.beta.assistants.create(
        name="Covid Agent",
        instructions="You are an expert in COVID-19 pandemic data. Use your knowledge base to answer queries.",
        model="gpt-4-turbo",
        tools=[{"type": "file_search"}],
    )
    # Link the vector store
    assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    )
    print(f"Assistant linked to vector store: {assistant.id}")
    return assistant


# Query the assistant
def query_assistant(assistant_id, query):
    # Create a thread for the assistant
    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role = "user",
        content = query
    )

    run = client.beta.threads.runs.create(
        thread_id = thread.id,
        assistant_id = assistant_id,
    )

    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)

    respmsg = client.beta.threads.messages.list(thread.id)
    return respmsg.data[0].content[0].text.value


# Main execution
if __name__ == "__main__":
    # Convert the CSV file to plain text and JSON
    convert_csv_to_text(csv_path, text_file_path)
    convert_csv_to_json(csv_path, json_file_path)

    # Upload the file to vector store (choose either text or JSON)
    vector_store_id = upload_file_to_vector_store(json_file_path, "text/plain")

    # Set up the assistant
    assistant = setup_assistant(vector_store_id)

    # Query the assistant
    query = "What are the properties for Slovakia on 25/10/2022?"
    response = query_assistant(assistant.id, query)
    print(response)
