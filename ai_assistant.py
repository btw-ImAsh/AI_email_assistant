
from simplegmail import Gmail
from simplegmail.query import construct_query
import os, datetime
import sqlite3
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
import requests
import json
from dotenv import load_dotenv


#contants
load_dotenv()
CREDENTIAL_PATH_CAL = "D:\\AI_mail_assistant\\credentials.json"
default_folder = "C:\\Users\\Public\\Downloads\\"
DB_PATH = 'emails.db'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
GOOGLE_SEARCH_ENGINE_ID=os.getenv('GOOGLE_SEARCH_ENGINE_ID')
GOOGLE_CUSTOM_SEARCH_API=os.getenv('GOOGLE_CUSTOM_SEARCH_API')

gmail = Gmail()
gc = GoogleCalendar(credentials_path=CREDENTIAL_PATH_CAL)

#This function will get our mails from Gmail inbox.

def get_emails():
    query_params = {
    "newer_than": (5, "day"),
    "unread": True
    }
    emails = []
    messages = gmail.get_messages(query=construct_query(query_params))

    attm_location= None
    for message in messages:
        sender = message.sender
        sender_name = sender.split("<")[0][:-1]
        sender_mail = sender.split("<")[1][:-1]
        if message.attachments:
            for attm in message.attachments:
                try:
                    default_path = f"{default_folder}{sender_mail}"
                    os.mkdir(default_path)
                except:
                    pass
                try:
                    attm.save(f"{default_path}\\{attm.filename}")
                except:
                    print("File already saved.")
                if attm_location is not None:
                    attm_location = attm_location + " , " + f"{default_path}\\{attm.filename}"
                else:
                    attm_location = f"{default_path}\\{attm.filename}"
        emails.append({
            'mail_id': message.id,
            'thread_id': message.thread_id,
            'subject' : message.subject,
            'recipient':message.recipient,
            'body': message.plain,
            'timestamp' : message.date,
            'sender_name': sender_name,
            'sender_mail': sender_mail,
            'attachments' : attm_location
        })
    return emails

#This will initialize our DB.

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails(
              mail_id TEXT PRIMARY KEY, 
              thread_id TEXT,
              subject TEXT,
              recipient TEXT,
              body TEXT,
              timestamp TEXT,
              sender_name TEXT,
              sender_mail TEXT,
              attachments TEXT)''')
    conn.commit()
    conn.close()

#This function will save our fetched emails individually into our DB.

def save_email(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO emails (mail_id, thread_id, subject, recipient, body, timestamp, sender_name, sender_mail, attachments)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (email['mail_id'], email['thread_id'], email['subject'], email["recipient"],  email['body'],
               email['timestamp'], email['sender_name'], email['sender_mail'], email["attachments"]))
    conn.commit()
    conn.close()

#This function will retrieve Emails Table from the DB.

def retrieve_mail():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute("""SELECT * FROM emails""").fetchall()
    for row in rows:
        print(row)
        print("\n")

#This function will get our locally installed LLM running to perform tasks.

def run_llama3_instruct(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False
        }
    )
    data = response.json()
    return data['response']

#Function that will parse our respective email and store the following info into a dictionary.
#Info containing Summary of the email, Identify the intent and lastly What action would user take.

def process_email(email):
    prompt = f"""
    You are an intelligent AI email assistant. Summarize this email, identify the intent (e.g. meeting request, question, reminder) 
    and order an action (reply, schedule).

    EMAIL:
    From: {email['sender_name']}
    Subject: {email['subject']}

    {email['body']}
    

    You must return only a json string without any other word in the output like:
    {{"summary": "...", "intent": "...", "action": "..."}}
    """
    processed_info={
        "summary" : "",
        "intent" : "",
        "action" : ""
    }
    response = run_llama3_instruct(prompt)
    try:
        data = json.loads(response)
        processed_info['summary'] = data.get('summary', '')
        processed_info['intent'] = data.get('intent', '')
        processed_info['action'] = data.get('action', '')
    except Exception as e:
        print("Failed to parse LLaMA 3 output:", response)
        processed_info['summary'] = ''
        processed_info['intent'] = 'unknown'
        processed_info['action'] = 'review'
    return processed_info

#This function will only focus on extracting time of the event discussed in the respective email.

def extract_time(email):
    time_prompt = f"""You are an intelligent AI assistant who does every task with high accuracy. 
        You have to extract date in yyyy-mm-dd and time in hh:mm in numerical values only from the message given below.
            
        You must return only a json string without any other word in the output like:
        {{"date": "...", "time": "..."}}
            
        MESSAGE:
        {email["subject"]}
        {email["body"]}
        """
    time_info  = {
        "date" : "",
        "time" : ""
    }
    processed_time = run_llama3_instruct(time_prompt)
    try:
        time_data = json.loads(processed_time)
        time_info["date"] = time_data.get('date', '')
        time_info["time"] = time_data.get('time', '')
    except:
        print("Failed to parse Time from mail:", processed_time)
        time_info["date"] = ""
        time_info["time"] = "unknown"
    return time_info

#Function that integrates Google Custom Search to our code.

def google_custom_search(query, num_results=2):
    cx = GOOGLE_SEARCH_ENGINE_ID
    api_key = GOOGLE_CUSTOM_SEARCH_API
    url = "https://www.googleapis.com/customsearch/v1"

    params = {
        'key': api_key,
        'cx': cx,
        'q': query,
        'num': num_results
    }

    response = requests.get(url, params=params)
    results = response.json()

    items = results.get('items', [])
    links = [{'title': item['title'], 'link': item['link'], 'snippet': item['snippet']} for item in items]

    return links

#This function will only focus on creating an calendar event scheduling the event on user's calendar. 

def create_calendar_event(summary, description, start_time):
    event = Event(
        summary=summary,
        description=description,
        start=start_time,
    )

    gc.add_event(event)
    print(f"[📅 Calendar] Event created. You can verify it but I asure you it's been taken care of.")

#This function will create a response after searching it on the internet and will gather knowlewdge of the matter.

def email_response_unknown(email):
    web_results = google_custom_search(query=email['subject'])
    snippets = "\n".join([f"{r['title']} - {r['link']}\n{r['snippet']}" for r in web_results])
    prompt = f"""
    You are an intelligent AI assistant. Send a polite, professional and to the point reply based on the email below and sign it with Scott Mccall.
    Here are some web results of the topic. {snippets}
    
    You must return only the body of email draft in html without any other word in the output.
    EMAIL:
    From: {email['sender_name']}
    Subject: {email['subject']}

    {email['body']}
    """
    reply = run_llama3_instruct(prompt)
    return reply.strip()

#This function will create a response of the recieved mail with the help of our LLM.

def email_response(email):
    prompt = f"""
    You are an intelligent AI assistant. Send a polite, professional and to the point reply based on the email below and sign it with Scott Mccall.
    
    You must return only the body of email draft in html without any other word in the output.
    
    EMAIL:
    From: {email["sender_name"]}
    Subject: {email["subject"]}

    {email["body"]}
    """
    reply = run_llama3_instruct(prompt)
    return reply.strip()

#This function will only focus on creating a slack message with the info user will pass as arguments and returning its status.
#Whether the message's sent or not. 

def send_to_slack(message):
    if SLACK_WEBHOOK_URL:
        response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        if response.status_code != 200:
            print(f"[Slack] Failed to send message: {response.text}")
        else:
            print("[Slack] Notification sent.")
    else:
        print("[Slack] Webhook URL not set.")

#This function will generate the response after scheduling our event with respective email.

def email_response_after_scheduled(email):
    prompt = f"""
    You are an intelligent AI assistant. Send a polite, professional and to the point reply after scheduling the meeting asked in the below email and sign it with Scott Mccall.

    You must return only the body of email draft in html without any other word in the output.
    
    EMAIL:
    From: {email['sender_name']}
    Subject: {email['subject']}

    {email['body']}
    """
    reply = run_llama3_instruct(prompt)
    return reply.strip()

# This function handles all the action that our AI will perform.

def handle_action(processed_info, email):
    action = processed_info["action"]     #Get the action which we'll perform.
    if action == 'schedule':
        print(f"[🗓️ Schedule] Scheduling with: {email['sender_name']}")
        extracted_time = extract_time(email=email)
        year = int(extracted_time["date"][:4])
        current = datetime.datetime.today()
        current_year = int(current.strftime("%Y"))
        final_year = current_year
        if year >= current_year:                    #Create the event that was requested and send the confirmation mail.
            final_year = year
            if extracted_time["time"]!="" and extracted_time["time"]!="00:00":
                set_hour = int(extracted_time["time"][:2])
                set_min = int(extracted_time["time"][3:5])
                set_day = int(extracted_time["date"][8:10])
                set_month = int(extracted_time["date"][5:7])
                start_time = datetime.datetime(year=final_year, month=set_month, day=set_day, hour=set_hour, minute=set_min)
                create_calendar_event(
                    summary=f"Meeting: " + email["sender_name"],
                    description = email['subject'],
                    start_time=start_time,
                )
            else:
                set_hour = 10
                set_min = 00
                set_day = int(extracted_time["date"][8:10])
                set_month = int(extracted_time["date"][5:7])
                start_time = datetime.datetime(year=final_year, month=set_month, day=set_day, hour=set_hour, minute=set_min)
                create_calendar_event(
                    summary=f"Meeting: {email['sender_name']}",
                    description=email['subject'],
                    start_time=start_time,
                )
            print(f"[✉️ Reply] Sending reply to: {email['sender_mail']}")
            after_schedule_body = email_response_after_scheduled(email)
            params = {
            "to": email["sender_mail"],
            "sender": email["recipient"],
            "subject": "Re: " + email["subject"],
            "msg_html": after_schedule_body,
            }
            try:
                gmail.send_message(**params)
            except:
                print("There is some error.")
        else:
            final_year = current_year
            if extracted_time["time"]!="" and extracted_time["time"]!="00:00":
                set_hour = int(extracted_time["time"][:2])
                set_min = int(extracted_time["time"][3:5])
                set_day = int(extracted_time["date"][8:10])
                set_month = int(extracted_time["date"][5:7])
                start_time = datetime.datetime(year=final_year, month=set_month, day=set_day, hour=set_hour, minute=set_min)
                create_calendar_event(
                    summary=f"Meeting: " + email["sender_name"],
                    description = email['subject'],
                    start_time=start_time,
                )
            else:
                set_hour = 10
                set_min = 00
                set_day = int(extracted_time["date"][8:10])
                set_month = int(extracted_time["date"][5:7])
                start_time = datetime.datetime(year=final_year, month=set_month, day=set_day, hour=set_hour, minute=set_min)
                create_calendar_event(
                    summary=f"Meeting: {email['sender_name']}",
                    description=email['subject'],
                    start_time=start_time,
                )
                print(f"[✉️ Reply] Sending reply to: {email['sender_mail']}")
                after_schedule_body = email_response_after_scheduled(email)
                params = {
                "to": email["sender_mail"],
                "sender": email["recipient"],
                "subject": "Re: " + email["subject"],
                "msg_html": after_schedule_body,
                }
                try:
                    gmail.send_message(**params)
                except:
                    print("There is some error.")
                    
    elif action == 'reply':                                           #This will reply with the response generated by our LLM.
        print(f"[✉️ Reply] Sending reply to: {email['sender_mail']}")
        reply_body = email_response(email)
        params = {
        "to": email["sender_mail"],
        "sender": email["recipient"],
        "subject": "Re: " + email["subject"],
        "msg_html": reply_body,
        }
        try:
            gmail.send_message(**params)
        except:
            print("There is some error.")
            
    else:                                                    #If the AI wont get the context of the mail. It will search on the web.
        print(f"[ℹ️ Review] Uncertain what to do with: {email['subject']}")                  #And reply accordingly.
        print("Scraping some websites to understand the situation.")
        print(f"[✉️ Reply] Sending reply to: {email['sender_mail']} accordingly")
        reply_unknown_body = email_response_unknown(email)
        params = {
        "to": email["sender_mail"],
        "sender": email["recipient"],
        "subject": "Re: " + email["subject"],
        "msg_html": reply_unknown_body,
        }
        try:
            gmail.send_message(**params)
        except:
            print("There is some error.")

    #This will create a slack dm for every mail

    slack_message = f"📧 *Email Summary:*\
    *From:* {email['sender_name']}\
    *Subject:* {email['subject']}\
    *Summary:* {processed_info['summary']}\
    *Intent:* {processed_info['intent']}\
    *Suggested Action:* {processed_info['action']}"
    send_to_slack(slack_message)


def main():
    init_db()
    emails = get_emails()
    for email in emails:
        save_email(email)
    while True:
        print("Hi Sir.. This is your AI assistant reporting on duty.\n")
        print("""<-------------------- List of commands -------------------->\n
          1. Get all the emails and reply accordingly.
          2. Fetch all emails from Database.
          3. Quit   
        """)
        try:
            input_user = int(input("Enter your choice: "))
            print("Your choice: ", input_user)
        except ValueError:
            print("Invalid input. Please enter an integer.")
        if input_user==1:
            for email in emails:
                processed_email = process_email(email)
                handle_action(processed_email, email)
        elif input_user==2:
            retrieve_mail()
        elif input_user==3:
            print("Thank you for believing in me. Adios")
            break

if __name__ == '__main__':
    main()
