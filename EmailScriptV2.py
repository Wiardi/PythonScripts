import tiktoken
import os
import win32com.client
import openai
import datetime

def estimate_cost(prompt_tokens, completion_tokens, model="gpt-4"):
    # Updated pricing as per OpenAI's API pricing (as of October 2023)
    if model == "gpt-4":
        prompt_cost_per_1k_tokens = 0.03   # $0.03 per 1K prompt tokens
        completion_cost_per_1k_tokens = 0.06  # $0.06 per 1K completion tokens
    elif model == "gpt-4-32k":
        prompt_cost_per_1k_tokens = 0.06   # $0.06 per 1K prompt tokens
        completion_cost_per_1k_tokens = 0.12  # $0.12 per 1K completion tokens
    elif model == "gpt-3.5-turbo":
        prompt_cost_per_1k_tokens = 0.0015  # $0.0015 per 1K prompt tokens
        completion_cost_per_1k_tokens = 0.002  # $0.002 per 1K completion tokens
    elif model == "gpt-3.5-turbo-16k":
        prompt_cost_per_1k_tokens = 0.003  # $0.003 per 1K prompt tokens
        completion_cost_per_1k_tokens = 0.004  # $0.004 per 1K completion tokens
    elif model == "gpt-4o-mini":
        prompt_cost_per_1k_tokens = 0.000075  # $0.000075 per 1K prompt tokens
        completion_cost_per_1k_tokens = 0.00030  # $0.00030 per 1K completion tokens
    else:
        # Default pricing if model is unrecognized
        prompt_cost_per_1k_tokens = 0.03
        completion_cost_per_1k_tokens = 0.06

    total_prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k_tokens
    total_completion_cost = (completion_tokens / 1000) * completion_cost_per_1k_tokens
    total_cost = total_prompt_cost + total_completion_cost
    return total_cost

def get_email_data(num_emails=1000):
    try:
        # Connect to Outlook
        outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
        
        # Access the inbox folder
        inbox = outlook.GetDefaultFolder(6)  # 6 refers to the inbox folder
        messages = inbox.Items
        total_emails = messages.Count  # Get the total number of emails
        messages.Sort("[ReceivedTime]", True)  # Sort by received time, newest first

        # Retrieve the latest emails
        email_data = []
        count = 0
        message = messages.GetFirst()
        while message and count < num_emails:
            # Get importance level
            importance = message.Importance  # 0: Low, 1: Normal, 2: High
            importance_str = {0: "Low", 1: "Normal", 2: "High"}.get(importance, "Normal")

            # Get the email body
            body = message.Body
            if body:
                body = body.strip().replace('\r', '').replace('\n', ' ')
                body = body[:5000]  # Limit body to first 500 characters
            else:
                body = "No content."

            # Append sender's name, subject, importance, and body
            email_data.append({
                "sender": message.SenderName,
                "subject": message.Subject,
                "importance": importance_str,
                "body": body
            })
            message = messages.GetNext()
            count += 1

        return email_data, total_emails  # Return both email data and total emails
    except Exception as e:
        print("Error accessing Outlook:", e)
        return [], 0

def generate_summary(email_data):
    try:
        # Prepare the data for the prompt
        summaries = []
        for item in email_data:
            sender = item['sender']
            subject = item['subject']
            importance = item['importance']
            body = item['body']

            if importance == "High":
                # Include body for urgent emails
                urgency = "[URGENT] "
                email_summary = f"From: {sender}\nSubject: {urgency}{subject}\nBody: {body}\n"
            else:
                # Do not include body for non-urgent emails
                email_summary = f"From: {sender}\nSubject: {subject}\n"

            summaries.append(email_summary)

        # Combine all email summaries
        combined_summaries = "\n".join(summaries)

        # Calculate token estimate using tiktoken
        encoding = tiktoken.encoding_for_model("gpt-4")
        prompt_tokens = len(encoding.encode(combined_summaries))

        # Check the length of the combined summaries
        if prompt_tokens > 80000:  # Adjust based on model's context limit
            return "The combined email content is too long to process."

        # Craft the prompt for ChatGPT
        prompt = (
            "Based on the following emails, summarize the most important topics and people I should focus on today, "
            "highlighting any urgent matters:\n\n"
            f"{combined_summaries}\n"
            "Provide a concise summary that helps me prioritize my (Ward van Genesen) responses."
        )

        # Recalculate prompt tokens including the full prompt
        prompt_tokens = len(encoding.encode(prompt))

        # Estimate completion tokens (max_tokens)
        completion_tokens = 500  # Adjust as needed

        # Estimate cost
        total_cost = estimate_cost(prompt_tokens, completion_tokens, model="gpt-4o-mini")

        # Retrieve the API key from the environment variable
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

        # Send the prompt to ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=completion_tokens,
            temperature=0.7,
        )

        # Extract the assistant's reply
        summary = response.choices[0].message.content.strip()

        # Include the cost estimate in the output
        print(f"Estimated cost of running the script: ${total_cost:.4f}")

        return summary

    except Exception as e:
        print("Error generating summary:", e)
        return "Could not generate a summary."

def write_to_daily_note(summary):
    import pathlib

    # **Update these variables according to your setup**
    vault_path = r"C:\Users\wardv\iCloudDrive\[4]Obsidian\Ward"  # Replace with your Obsidian vault path
    daily_notes_folder = "Daily Notes"  # Replace if your daily notes are in a different folder

    # Get today's date
    today = datetime.date.today()
    # Format the filename, assuming "YYYY-MM-DD.md"
    filename = today.strftime("%Y-%m-%d") + ".md"

    # Full path to the daily note file
    daily_note_path = os.path.join(vault_path, daily_notes_folder, filename)

    # Write the summary to the daily note
    try:
        # Check if the daily note file exists
        if not os.path.exists(daily_note_path):
            # Create the file if it doesn't exist
            with open(daily_note_path, 'w', encoding='utf-8') as f:
                f.write(f"# {today.strftime('%Y-%m-%d')}\n\n")  # Optionally write a title

        # Append the summary to the daily note
        with open(daily_note_path, 'a', encoding='utf-8') as f:
            f.write("\n## Email Summary\n\n")
            f.write(summary)
            f.write("\n")
        print(f"Summary successfully written to {daily_note_path}")
    except Exception as e:
        print("Error writing to daily note:", e)

def main():
    # Fetch email data including sender, subject, importance, and body
    email_data, total_emails = get_email_data()

    print(f"Total number of emails in the inbox: {total_emails}")

    if email_data:
        # Generate a summary using ChatGPT
        summary = generate_summary(email_data)

        # Write the summary to the Obsidian daily note
        write_to_daily_note(summary)

        print(summary)
    else:
        print("No emails to process.")

if __name__ == "__main__":
    main()
