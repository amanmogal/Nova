"""
Setup script for the autonomous Notion task management agent.
This script initializes the required databases and environment.
"""
import os
import sys
import json
from pathlib import Path
import time
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import chromadb
from notion_client import Client
from supabase import create_client

from src.schema.notion_schemas import NotionDatabaseSchema

# Load environment variables
load_dotenv()


def setup_notion():
    """Set up or verify Notion databases."""
    print("Setting up Notion integration...")
    
    # Check for required environment variables
    notion_api_key = os.getenv("NOTION_API_KEY")
    if not notion_api_key:
        print("ERROR: NOTION_API_KEY environment variable not set.")
        print("Please add your Notion API key to the .env file.")
        return False
    
    try:
        # Initialize Notion client
        client = Client(auth=notion_api_key)
        
        # Test connection
        user = client.users.me()
        print(f"Successfully connected to Notion as: {user['name']}")
        
        # Check if database IDs are provided
        tasks_db_id = os.getenv("NOTION_TASKS_DATABASE_ID")
        routines_db_id = os.getenv("NOTION_ROUTINES_DATABASE_ID")
        
        if tasks_db_id:
            print(f"Tasks database ID provided: {tasks_db_id}")
            # Verify database exists and has correct schema
            try:
                db = client.databases.retrieve(tasks_db_id)
                print(f"Found tasks database: {db['title'][0]['plain_text']}")
            except Exception as e:
                print(f"Error accessing tasks database: {str(e)}")
                tasks_db_id = None
        
        if routines_db_id:
            print(f"Routines database ID provided: {routines_db_id}")
            # Verify database exists and has correct schema
            try:
                db = client.databases.retrieve(routines_db_id)
                print(f"Found routines database: {db['title'][0]['plain_text']}")
            except Exception as e:
                print(f"Error accessing routines database: {str(e)}")
                routines_db_id = None
        
        # If database IDs are not provided or invalid, offer to create them
        if not tasks_db_id or not routines_db_id:
            print("\nWould you like to create the required Notion databases? (y/n)")
            choice = input().lower()
            
            if choice == 'y':
                # Get parent page ID
                parent_page_id = input("Enter the ID of a parent page where databases will be created: ")
                
                # Create tasks database if needed
                if not tasks_db_id:
                    try:
                        schema = NotionDatabaseSchema.tasks_database_schema()
                        tasks_db = client.databases.create(
                            parent={"page_id": parent_page_id},
                            title=[{"text": {"content": "Tasks"}}],
                            properties=schema
                        )
                        tasks_db_id = tasks_db["id"]
                        print(f"Created tasks database with ID: {tasks_db_id}")
                        print("Please add this ID to your .env file as NOTION_TASKS_DATABASE_ID")
                    except Exception as e:
                        print(f"Error creating tasks database: {str(e)}")
                
                # Create routines database if needed
                if not routines_db_id:
                    try:
                        schema = NotionDatabaseSchema.routines_database_schema()
                        routines_db = client.databases.create(
                            parent={"page_id": parent_page_id},
                            title=[{"text": {"content": "Routines & Preferences"}}],
                            properties=schema
                        )
                        routines_db_id = routines_db["id"]
                        print(f"Created routines database with ID: {routines_db_id}")
                        print("Please add this ID to your .env file as NOTION_ROUTINES_DATABASE_ID")
                    except Exception as e:
                        print(f"Error creating routines database: {str(e)}")
            else:
                print("Skipping database creation.")
                print("Please add the database IDs to your .env file manually.")
        
        return True
    except Exception as e:
        print(f"Error setting up Notion: {str(e)}")
        return False


def setup_vector_db():
    """Set up or verify the vector database."""
    print("\nSetting up vector database (ChromaDB)...")
    
    # Define ChromaDB path
    chroma_path = os.getenv("CHROMA_DB_PATH", "./data/chroma")
    
    # Create directory if it doesn't exist
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Check if collections exist, create them if they don't
        try:
            tasks_collection = client.get_collection("notion_tasks")
            print(f"Found 'notion_tasks' collection with {tasks_collection.count()} items")
        except ValueError:
            tasks_collection = client.create_collection("notion_tasks")
            print("Created 'notion_tasks' collection")
        
        try:
            routines_collection = client.get_collection("notion_routines")
            print(f"Found 'notion_routines' collection with {routines_collection.count()} items")
        except ValueError:
            routines_collection = client.create_collection("notion_routines")
            print("Created 'notion_routines' collection")
        
        return True
    except Exception as e:
        print(f"Error setting up ChromaDB: {str(e)}")
        return False


def setup_supabase():
    """Set up or verify Supabase database."""
    print("\nSetting up Supabase integration...")
    
    # Check for required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("ERROR: Supabase environment variables not set.")
        print("Please add SUPABASE_URL and SUPABASE_KEY to the .env file.")
        print("You can get these from your Supabase project settings.")
        return False
    
    try:
        # Initialize Supabase client
        client = create_client(supabase_url, supabase_key)
        
        # Test connection by making a simple query
        response = client.table("agent_state").select("*").limit(1).execute()
        print("Successfully connected to Supabase")
        
        return True
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        print("\nPlease ensure that the following tables exist in your Supabase project:")
        print(" - agent_state: For storing the agent's state")
        print(" - agent_actions: For logging actions taken by the agent")
        print(" - learned_preferences: For storing learned user preferences")
        
        print("\nWould you like to see the SQL to create these tables? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            print("\n--- SQL to create required tables ---")
            print("""
CREATE TABLE agent_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state JSONB,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE agent_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type TEXT,
    details JSONB,
    status TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE learned_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    preference_type TEXT,
    preference_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
            """)
        
        return False


def main():
    """Main setup function."""
    print("===== Notion Task Management Agent Setup =====\n")
    
    # Check for .env file
    if not os.path.exists(".env") and not os.path.exists("../.env"):
        print("WARNING: No .env file found.")
        print("Creating example .env file. Please edit it with your credentials.")
        
        # Copy from env.example
        if os.path.exists("env.example"):
            with open("env.example", "r") as example, open(".env", "w") as env:
                env.write(example.read())
            print("Created .env file from env.example")
        else:
            print("No env.example file found. Please create a .env file manually.")
    
    # Setup components
    notion_ok = setup_notion()
    vector_db_ok = setup_vector_db()
    supabase_ok = setup_supabase()
    
    # Summary
    print("\n===== Setup Summary =====")
    print(f"Notion Integration: {'✓ OK' if notion_ok else '✗ Failed'}")
    print(f"Vector Database: {'✓ OK' if vector_db_ok else '✗ Failed'}")
    print(f"Supabase Integration: {'✓ OK' if supabase_ok else '✗ Failed'}")
    
    if notion_ok and vector_db_ok and supabase_ok:
        print("\n✓ Setup completed successfully!")
        print("You can now run the agent with: python src/agent.py")
    else:
        print("\n✗ Setup incomplete. Please fix the issues above and try again.")
    

if __name__ == "__main__":
    main() 