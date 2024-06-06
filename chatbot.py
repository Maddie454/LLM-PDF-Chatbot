# An example LLM chatbot using Cohere API and Streamlit that references a PDF
# Adapted from the StreamLit OpenAI Chatbot example - https://github.com/streamlit/llm-examples/blob/main/Chatbot.py

import streamlit as st
import cohere
import fitz # An alias for PyMuPDF
import pandas as pd
import csv
from PIL import Image
import datetime
import re



image = Image.open('docs/logo.png')

csv_path = 'docs/261103@hkis.edu/hk.ics_export.csv'

# Handle PDF or CSV 
def documents_from_file(file_path):

  ext = os.path.splitext(file_path)[1]

  if ext == '.pdf':  
    return pdf_to_documents(file_path) 
  elif ext == '.csv':
    return csv_to_documents(file_path)

  
# New CSV function   
def csv_to_documents(csv_path):

  documents = []

  with open(csv_path) as f:
    reader = csv.DictReader(f)

    for row in reader:
     
      # parse CSV
      
      title = row["Start Time"] 
      content = row["Event Name"] 
      end_time = row["End Time"] 
      location = row["Location"]
      description = row["Description"]
      organizer = row["Organizer"]
      attendees = row["Attendees"]



      document = {"Start Time": title, "Event Name": content,"End Time": end_time,"Location": location,"Description":description, "Organizer":organizer,"Attendees":attendees}

      documents.append(document)
      
  return documents
def pdf_to_documents(pdf_path):
    """
    Converts a PDF to a list of 'documents' which are chunks of a larger document that can be easily searched 
    and processed by the Cohere LLM. Each 'document' chunk is a dictionary with a 'title' and 'snippet' key
    
    Args:
        pdf_path (str): The path to the PDF file.
    
    Returns:
        list: A list of dictionaries representing the documents. Each dictionary has a 'title' and 'snippet' key.
        Example return value: [{"title": "Page 1 Section 1", "snippet": "Text snippet..."}, ...]
    """

    doc = fitz.open(pdf_path)
    documents = []
    text = ""
    chunk_size = 1000
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        part_num = 1
        for i in range(0, len(text), chunk_size):
            documents.append({"title": f"Page {page_num + 1} Part {part_num}", "snippet": text[i:i + chunk_size]})
            part_num += 1
    return documents
# Add a sidebar to the Streamlit app
with st.sidebar:
    st.title("🗓️📝 Task Sync 🎯✅")
    st.sidebar.image(image, width=150)
    d = st.date_input("What day is it today?", value=None)
    st.write("Today is:", d)
    t = st.time_input("What time is it right now", value=None)
    st.write("The time is:", t)
    cohere_api_key = st.text_input("Enter Cohere API Key")
    client = cohere.Client(api_key=cohere_api_key)
    cohere_api_key = st.text_input(
    "API Key", 
    type="password",
    key="cohere_api_key"
  )

  st.markdown("[Get API key](link)")



    if hasattr(st, "secrets"):
        cohere_api_key = st.secrets["COHERE_API_KEY"]
        # st.write("API key found.")
        

    else:
        cohere_api_key = st.text_input("Cohere API Key", key="chatbot_api_key", type="password")
        st.markdown("[Get a Cohere API Key](https://dashboard.cohere.ai/api-keys)")
    
    my_documents = []
    selected_doc = st.selectbox("Select your timetable", ["My schedule this week", "Person#2 schedule next week"])
    if selected_doc == "My schedule this week":
        my_documents = csv_to_documents('docs/csv_file.csv')
    elif selected_doc == "Person#2 schedule next week":    
        my_documents = csv_to_documents('docs/csv_file.csv')
    else:
        my_documents = csv_to_documents('docs/csv_file.csv')

    # st.write(f"Selected document: {selected_doc}")
st.title("🗓️📝 Task Sync 🎯✅")
# Set the title of the Streamlit app



# Initialize the chat history with a greeting message
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "text": "Hi, I'm task sync my job is to help you organize and remind you what you need to do today.Please input your date and time in the sidebar so i can help you!!"}]

# Display the chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["text"])

  
# Get user input
if prompt := st.chat_input():
    # Stop responding if the user has not added the Cohere API key
    if not cohere_api_key:
        st.info("Please add your Cohere API key to continue.")
        st.stop()

    # Create a connection to the Cohere API
    client = cohere.Client(api_key=cohere_api_key)
    
    # Display the user message in the chat window
    st.chat_message("user").write(prompt)

    preamble = f"""You are task sync and your job is to tell the user what they need to do today,according to the date {d} and {t}chosen please match your response according to the title Start Time row date and then answer the users questions using the content Event name as well as
      other information such as location,description, organizer as requested by the user. Also please list your response in chrnological order. Only include text in plain english, time, or room number that are are answering the users question
    """

    # Send the user message and pdf text to the model and capture the response
    response = client.chat(chat_history=st.session_state.messages,
                           message=prompt,
                           documents=my_documents,
                           prompt_truncation='AUTO',
                           preamble=preamble)
    
    # Add the user prompt to the chat history
    st.session_state.messages.append({"role": "user", "text": prompt})
    
    # Add the response to the chat history
    msg = response.text
    st.session_state.messages.append({"role": "assistant", "text": msg})

    # Write the response to the chat window
    st.chat_message("assistant").write(msg)