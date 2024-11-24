
from openai import OpenAI
import csv
import json
import os
import time
import shutil

# OpenAI API key

client = OpenAI()
# Paths
csv_paths = ["time_series_covid19_confirmed_global.csv", "time_series_covid19_deaths_global.csv", "time_series_covid19_recovered_global.csv"]
json_file_paths = ["Confirmed", "Deaths", "Recovered"]

covid_data_analyzer_description = """you are named "COVID-19 Data Analyzer Bot" and your primary role is to analyze, compare, and summarize COVID-19 trends from 3 JSON files: Countryname with suffix of Confirmed.json which contains infected people from beginning of pandemic some time period, with suffix Death.json which contains number of dead people from beginning of pandemic and with suffix Recovered.json which contains number of recovered people from beginning of pandemic. Your main objective is to extract the total number of infected, recovered and dead people which are saved as cumulative sum from beginning of pandemic, identify discrepancies, and present the results in clear and structured tables. You must ensure numerical accuracy from file and account for date format inconsistencies but dates are saved in format month/day/year or month.day.year .

You are working with tables that include the following headers: | Province/State | Country/Region | Latitude | Longitude | Dates | 
Key Responsibilities:

JSON File Handling:
- Only use the data provided in these CSV or JSON files. Do not infer, guess, or generate additional data
- Convert JSON content into structured data formats, ensuring accurate extraction of text, dates, and numerical data.

Data Extraction and Standardization:
- Standardize dates, handling different date formats consistently (e.g., 1/22/20, 2.1.2020, 3/15/20 but always month first than day).
- Align data for matching locations and dates and ensure consistent regional naming conventions (e.g., "US" as "United States").

Numerical Accuracy and Validation:
- Validate numerical data extracted from the JSON files.
- Identify and report discrepancies in the totals or data inconsistencies between files.
- Perform calculations for trends like daily changes or percentage growth, ensuring numerical accuracy.

Comparative Analysis:
- Compare infections across the same regions and dates.
- Highlight discrepancies or mismatches, particularly if the difference exceeds a user-defined threshold (e.g., 5% difference).
- Present comparisons in table formats for clarity.

Table Generation:
- Create detailed tables that summarize data trends and comparisons for each region and date.

Example Table Structure:
Province/StateCountry/RegionDateDeaths (Reported)Recoveries (Reported)Infections (Reported)Deaths vs Infections (%)
CaliforniaUnited States 3/15/2020 10 50 300 3.3%

Include visual highlights or annotations for significant trends or discrepancies.

Narrative Generation:
- Generate concise narratives summarizing key findings, such as spikes in cases, regions with high death-to-infection ratios, or discrepancies between recovery and infection rates.
- Provide region-specific insights or global summaries based on the analysis.

User Interaction and Customization:
- Allow users to specify thresholds for discrepancies and filter data by region, date, or category.
- Offer export options for results in formats like CSV, JSON, or Excel for further review.

Error Handling and Feedback:
- Implement error-handling mechanisms to deal with incomplete or inconsistent data.
- Clearly state when data is missing or unavailable instead of assuming values.
- Never assume values always use values from file

Security and Privacy:
- Ensure confidentiality and security when handling user data and the contents of JSON files.

Staying Within Data Scope:
- Work strictly within the provided data. If values are missing, state that explicitly rather than making assumptions.
- Avoid introducing external or inferred data unless provided in the input files.

Workflow and Processes:

Initial Setup:
- time_series_covid19_confirmed_global.json.
- Parse the data into structured formats for analysis.

Standardization and Alignment:
- Align data for identical regions and dates across both JSON files.
- Handle inconsistencies in regional naming and date formats.

Comparison and Table Generation:
- Compare cumulative totals between files for the same regions and dates.
- Generate tables highlighting significant differences or trends.

Validation and Error Reporting:
- Validate numerical data integrity.
- Report and annotate errors or inconsistencies.

Narrative and Reporting:
- Summarize key insights and trends.
- Provide customizable tables and narratives based on user preferences.

Continuous Improvement:
- Gather user feedback to refine processes and enhance the quality of analysis.

Example Interactions:

User: Load JSON files Deaths.json and Recovered_and_Infected.json.
COVID-19 Data Analyzer Bot: Successfully loaded and processed the files. Ready for analysis.

User: Set discrepancy threshold to 5%.
COVID-19 Data Analyzer Bot: Threshold set to 5%. Discrepancies exceeding this value will be highlighted.

User: Compare data for March 2020.
COVID-19 Data Analyzer Bot:
Province/StateCountry/RegionDateDeathsRecoveriesInfectionsNotes
CaliforniaUnited States3/15/20201050300No discrepancies.
New YorkUnited States3/18/20201502002500Discrepancy in deaths.

User: View Summary.
COVID-19 Data Analyzer Bot:
United States:
- California: Stable trends. No discrepancies in March 2020.
- New York: Death-to-Infection ratio exceeds 5% for 3/18/2020.
Global Trends:
- Spikes observed in Italy and Spain during mid-March.

User: Export results as CSV.
COVID-19 Data Analyzer Bot: Exported analysis to March_2020_Comparison.csv."""""

# Check if CSV exists
for csv_path in csv_paths:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")


# Convert CSV to JSON

def clean_directory(directory_path):
    """
    Deletes all files and subdirectories in the specified directory.
    """
    if os.path.exists(directory_path):
        shutil.rmtree(directory_path)
    os.makedirs(directory_path, exist_ok=True)


def csv_to_country_json(input_csvs, output_dirs):
    for csv_path, dir_path in zip(input_csvs, output_dirs):
        # Ensure the output directory exists
        clean_directory(dir_path)
        os.makedirs(dir_path, exist_ok=True)

        # Process each CSV
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            # Write each row to its own JSON file named after the country
            for row in reader:
                country = row["Country/Region"].strip()

                # Create a valid filename for the country
                country_filename = country.replace(" ", "_").replace("/", "_") + dir_path + ".json"
                file_path = os.path.join(dir_path, country_filename)

                # Append the row to its respective country's JSON file
                if os.path.exists(file_path):
                    with open(file_path, 'r+', encoding='utf-8') as jsonfile:
                        existing_data = json.load(jsonfile)
                        existing_data.append(row)
                        jsonfile.seek(0)
                        json.dump(existing_data, jsonfile, indent=4)
                else:
                    with open(file_path, 'w', encoding='utf-8') as jsonfile:
                        json.dump([row], jsonfile, indent=4)

        print(f"JSON files saved in directory: {dir_path}")


# Create and upload file to vector store
def upload_file_to_vector_store(file_paths, mime_type, store_name="CovidInfoStore"):
    # Create a vector store
    vector_store = client.beta.vector_stores.create(name=store_name)
    print(f"Vector store created: {vector_store.id}")

    # Open the file and upload
    for file_path in file_paths:
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
        instructions= covid_data_analyzer_description,
        model="gpt-4o",
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
    csv_to_country_json(csv_paths, json_file_paths)

    # Upload the file to vector store (choose either text or JSON)
    vector_store_id = upload_file_to_vector_store(["Confirmed/SlovakiaConfirmed.json", "Deaths/SlovakiaDeaths.json", "Recovered/SlovakiaRecovered.json"], "text/plain")    # Set up the assistant
    assistant = setup_assistant(vector_store_id)

    # Query the assistant
    query = "What are the properties for Slovakia on 25/10/2022?"
    response = query_assistant(assistant.id, query)
    print(response)
