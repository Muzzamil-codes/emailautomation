import discord
from discord.ext import commands
import json
import os
from typing import Dict, List, Any
import re
import subprocess
import datetime
from dotenv import load_dotenv
import sys
import io
import threading
from src.sales_personalized_email.main import run
import asyncio

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Get token from environment variable
PREFIX = 'DuDe '  # Command prefix

# Initialize the bot with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Path to JSON file for storing business data (legacy)
JSON_FILE = 'businesses.json'

# Path to folder for storing individual business JSON files
COLDLEADS_FOLDER = 'coldleads'

# Global variable to track staged files
STAGED_FILES = set()

# Initialize JSON file if it doesn't exist
def initialize_json_file():
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as f:
            json.dump([], f)
    
    # Also create coldleads folder if it doesn't exist
    if not os.path.exists(COLDLEADS_FOLDER):
        os.makedirs(COLDLEADS_FOLDER)

# Add business data to coldleads folder as individual JSON file
async def add_business(business_data: Dict[str, Any]):    
    try:
        with open(JSON_FILE, 'r') as f:
            businesses = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        businesses = []
    
    businesses.append(business_data)
    
    with open(JSON_FILE, 'w') as f:
        json.dump(businesses, f, indent=4)
    
    # Count the total number of files in the coldleads folder
    json_files = [f for f in os.listdir(COLDLEADS_FOLDER) if f.endswith('.json')]
    return len(json_files)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    initialize_json_file()

@bot.command(name='addlead')
async def add_business_command(ctx, *, data):
    """
    Adds a business to the database and saves it as an individual JSON file.
    Usage: DuDe addlead company="Company Name" industry="Industry" business_type="Business Type" location="Location"
    """
    try:
        # Extract key-value pairs using regex
        pattern = r'(\w+)="([^"]+)"'
        matches = re.findall(pattern, data)
        
        business_data = {}
        for key, value in matches:
            business_data[key] = value
        
        # Check for required fields
        required_fields = ['company', 'industry', 'business_type', 'location']
        missing_fields = [field for field in required_fields if field not in business_data]
        
        if missing_fields:
            missing_str = ", ".join(missing_fields)
            await ctx.send(f"Error: Missing required fields: {missing_str}")
            return
        
        # Add timestamp to the business data
        business_data['added_at'] = datetime.datetime.now().isoformat()
        await add_business(business_data)
        # count = await add_business(business_data)
        await ctx.send(f"Business '{business_data['company']}' added successfully!")
    
    except Exception as e:
        await ctx.send(f"Error adding business: {str(e)}\nUsage: DuDe addlead company=\"Company Name\" industry=\"Industry\" business_type=\"Business Type\" location=\"Location\"")

@bot.command(name='listrawleads')
async def list_raw_businesses(ctx):
    """Lists all businesses in the legacy database file."""
    try:
        with open(JSON_FILE, 'r') as f:
            businesses = json.load(f)
        
        if not businesses:
            await ctx.send("No leads found in the database.")
            return
        
        response = f"Total leads: {len(businesses)}\n\n"
        for i, business in enumerate(businesses, 1):
            response += f"{i}. {business['company']} - {business['industry']} ({business['location']})\n"
            
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"Error loading businesses: {str(e)}")

@bot.command(name='listcoldleads')
async def list_cold_leads(ctx):
    """Lists all JSON files in the coldleads folder."""
    try:
        # Create coldleads folder if it doesn't exist
        if not os.path.exists(COLDLEADS_FOLDER):
            os.makedirs(COLDLEADS_FOLDER)
            await ctx.send(f"Created '{COLDLEADS_FOLDER}' folder. No JSON files found yet.")
            return
        
        # Get all JSON files in the folder
        json_files = [f for f in os.listdir(COLDLEADS_FOLDER) if f.endswith('.json')]
        
        if not json_files:
            await ctx.send(f"No JSON files found in the '{COLDLEADS_FOLDER}' folder.")
            return
        
        # List all JSON files
        response = f"Found {len(json_files)} JSON file(s) in '{COLDLEADS_FOLDER}' folder:\n\n"
        for i, file in enumerate(json_files, 1):
            # Try to read company information from each file
            file_path = os.path.join(COLDLEADS_FOLDER, file)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and 'company' in data[0]:
                        company_name = data[0]['company']
                        response += f"{i}. {file} - Contains data for {company_name}\n"
                    else:
                        response += f"{i}. {file}\n"
            except Exception:
                # If can't read or parse file, just list the filename
                response += f"{i}. {file}\n"
            
        await ctx.send(response)
    except Exception as e:
        await ctx.send(f"Error listing JSON files: {str(e)}")

@bot.command(name='showlead')
async def show_lead(ctx, file_number: int = None, file_name: str = None):
    """
    Displays the contents of a specific JSON file from the coldleads folder.
    Usage: 
    - DuDe showlead 3 (displays the 3rd file from the listcoldleads command)
    - DuDe showlead filename="company_name_20240620_123045.json" (displays the file with the exact name)
    """
    try:
        # Create coldleads folder if it doesn't exist
        if not os.path.exists(COLDLEADS_FOLDER):
            os.makedirs(COLDLEADS_FOLDER)
            await ctx.send(f"Created '{COLDLEADS_FOLDER}' folder. No JSON files found yet.")
            return
        
        # Get all JSON files in the folder
        json_files = [f for f in os.listdir(COLDLEADS_FOLDER) if f.endswith('.json')]
        
        if not json_files:
            await ctx.send(f"No JSON files found in the '{COLDLEADS_FOLDER}' folder.")
            return
        
        # Determine which file to display
        target_file = None
        
        # If file_name is provided (in the format filename="file.json")
        if file_name:
            # Extract the actual filename from the parameter
            match = re.match(r'filename="([^"]+)"', file_name)
            if match:
                file_name = match.group(1)
                
            if file_name in json_files:
                target_file = file_name
            else:
                # Try partial match if exact match not found
                matching_files = [f for f in json_files if file_name.lower() in f.lower()]
                if matching_files:
                    target_file = matching_files[0]
                    if len(matching_files) > 1:
                        await ctx.send(f"Multiple files match '{file_name}'. Showing the first match: {target_file}")
                else:
                    await ctx.send(f"No file found matching '{file_name}' in the '{COLDLEADS_FOLDER}' folder.")
                    return
        
        # If file_number is provided (index in the list)
        elif file_number is not None:
            if 1 <= file_number <= len(json_files):
                target_file = json_files[file_number - 1]
            else:
                await ctx.send(f"Invalid file number. Please use a number between 1 and {len(json_files)}.")
                return
        
        # If neither is provided
        else:
            await ctx.send("Please specify either a file number or a filename. Example: `DuDe showlead 3` or `DuDe showlead filename=\"company_name.json\"`")
            return
        
        # Read and display the file contents
        file_path = os.path.join(COLDLEADS_FOLDER, target_file)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Format the JSON data for better display
                formatted_data = json.dumps(data, indent=2)
                
                # Check if the formatted data is too long for Discord's message limit
                if len(formatted_data) > 1900:  # Discord's limit is 2000, keeping some margin
                    # Truncate and show important fields
                    response = f"**File: {target_file}** (Showing summary due to large size)\n\n"
                    if isinstance(data, list) and len(data) > 0:
                        lead = data[0]
                        response += "```json\n"
                        for key, value in lead.items():
                            response += f"{key}: {value}\n"
                        response += "```"
                    else:
                        response += "```json\n" + formatted_data[:1800] + "\n... (truncated) ```"
                else:
                    response = f"**File: {target_file}**\n\n```json\n{formatted_data}\n```"
                
                await ctx.send(response)
        except Exception as e:
            await ctx.send(f"Error reading file '{target_file}': {str(e)}")
    
    except Exception as e:
        await ctx.send(f"Error displaying lead: {str(e)}")

@bot.command(name='help_leads')
async def help_business(ctx):
    """Shows help information for business commands."""
    help_text = """
**Business Bot Commands:**
`DuDe addlead company="Company Name" industry="Industry" business_type="Business Type" location="Location"` - Add a new business lead
`DuDe listcoldleads` - List all JSON files in the coldleads folder
`DuDe showlead 3` - Display contents of the 3rd file from the listcoldleads command
`DuDe showlead filename="company_name_20240620_123045.json"` - Display contents of a specific file
`DuDe listrawleads` - List all businesses in the legacy database file
`DuDe help_leads` - Show this help message

**Examples:**
`DuDe addlead company="Al Afaq Insurance Brokers" industry="Insurance Brokage Providers" business_type="Insurance Brokers" location="Dubai, UAE"`
`DuDe showlead 1` - Show the first lead file
`DuDe showlead filename="al_afaq"` - Show the lead file containing "al_afaq" in the filename
    """
    await ctx.send(help_text)

@bot.command(name='stagefile')
async def stage_files(ctx, *files):
    """
    Stages files from the coldleads folder, similar to git add.
    Usage: 
    - DuDe stagefile . (stages all files)
    - DuDe stagefile file1.json file2.json (stages specific files)
    """
    global STAGED_FILES
    
    # Create coldleads folder if it doesn't exist
    if not os.path.exists(COLDLEADS_FOLDER):
        os.makedirs(COLDLEADS_FOLDER)
        await ctx.send(f"Created '{COLDLEADS_FOLDER}' folder. No JSON files found yet.")
        return
    
    # Get all JSON files in the folder
    json_files = [f for f in os.listdir(COLDLEADS_FOLDER) if f.endswith('.json')]
    
    if not json_files:
        await ctx.send(f"No JSON files found in the '{COLDLEADS_FOLDER}' folder.")
        return
    
    # If "." is provided, stage all files
    if len(files) == 1 and files[0] == '.':
        before_count = len(STAGED_FILES)
        STAGED_FILES.update(json_files)
        new_count = len(STAGED_FILES) - before_count
        await ctx.send(f"Staged all {len(json_files)} files. {new_count} new files added to staging area.")
        return
    
    # Stage specific files
    staged_count = 0
    not_found = []
    
    for file in files:
        # If exact match
        if file in json_files:
            STAGED_FILES.add(file)
            staged_count += 1
        else:
            # Try partial match
            matches = [f for f in json_files if file.lower() in f.lower()]
            if matches:
                STAGED_FILES.update(matches)
                staged_count += len(matches)
                if len(matches) > 1:
                    await ctx.send(f"Multiple files match '{file}'. Added {len(matches)} files to staging area.")
            else:
                not_found.append(file)
    
    response = f"Staged {staged_count} file(s)."
    if not_found:
        response += f" Could not find these files: {', '.join(not_found)}"
    
    await ctx.send(response)

@bot.command(name='add_gmail')
async def add_gmail(ctx, filename: str = None, gmail: str = None):
    """
    Adds a 'gmail' field to the first object in the specified JSON file inside the coldleads folder.
    Usage: DuDe add_gmail filename.json someone@example.com
    """
    if not filename or not gmail:
        await ctx.send("Usage: DuDe add_gmail filename.json someone@example.com")
        return

    file_path = os.path.join(COLDLEADS_FOLDER, filename)

    if not os.path.exists(file_path):
        await ctx.send(f"Error: File '{filename}' not found in '{COLDLEADS_FOLDER}'.")
        return

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        data["email"] = gmail

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        await ctx.send(f"Successfully added Gmail '{gmail}' to '{filename}'.")
    except Exception as e:
        await ctx.send(f"Error updating file: {str(e)}")

@bot.command(name='unstagefile')
async def unstage_files(ctx, *files):
    """
    Removes files from the staging area, similar to git reset.
    Usage: 
    - DuDe unstagefile . (unstages all files)
    - DuDe unstagefile file1.json file2.json (unstages specific files)
    """
    global STAGED_FILES
    
    if not STAGED_FILES:
        await ctx.send("No files are currently staged.")
        return
    
    # If "." is provided, unstage all files
    if len(files) == 1 and files[0] == '.':
        count = len(STAGED_FILES)
        STAGED_FILES.clear()
        await ctx.send(f"Unstaged all {count} files. Staging area is now empty.")
        return
    
    # Unstage specific files
    unstaged_count = 0
    not_found = []
    
    for file in files:
        # If exact match
        if file in STAGED_FILES:
            STAGED_FILES.remove(file)
            unstaged_count += 1
        else:
            # Try partial match
            matches = [f for f in STAGED_FILES if file.lower() in f.lower()]
            if matches:
                for match in matches:
                    STAGED_FILES.remove(match)
                unstaged_count += len(matches)
                if len(matches) > 1:
                    await ctx.send(f"Multiple files match '{file}'. Removed {len(matches)} files from staging area.")
            else:
                not_found.append(file)
    
    response = f"Unstaged {unstaged_count} file(s)."
    if not_found:
        response += f" Could not find these files in staging area: {', '.join(not_found)}"
    
    await ctx.send(response)

@bot.command(name='liststaged')
async def list_staged_files(ctx):
    """Lists all files currently in the staging area."""
    global STAGED_FILES
    
    if not STAGED_FILES:
        await ctx.send("No files are currently staged.")
        return
    
    response = f"Currently staged files ({len(STAGED_FILES)}):\n\n"
    for i, file in enumerate(sorted(STAGED_FILES), 1):
        response += f"{i}. {file}\n"
    
    await ctx.send(response)

@bot.command(name='commit')
async def commit_files(ctx, *, message=None):
    """
    Commits the staged files.
    Usage: DuDe commit message="Your commit message here"
    """
    global STAGED_FILES
    
    if not STAGED_FILES:
        await ctx.send("No files are staged for commit. Use `DuDe stagefile` to stage files first.")
        return
    
    # Extract commit message if provided
    commit_message = "No message provided"
    if message:
        match = re.match(r'message="([^"]+)"', message)
        if match:
            commit_message = match.group(1)
    
    # This is a placeholder for future implementation
    # For now, just acknowledge the staged files
    files_list = list(STAGED_FILES)
    file_count = len(files_list)
    
    # TODO: Implement actual commit functionality
    
    # Clear the staging area after commit
    STAGED_FILES.clear()
    
    await ctx.send(f"Committed {file_count} files with message: \"{commit_message}\"\n" +
                   f"Files that would be processed: {', '.join(files_list)}\n" +
                   "Note: This is a placeholder. The actual commit function is not yet implemented.")

@bot.command(name='help_git')
async def help_git(ctx):
    """Shows help information for Git-like commands."""
    help_text = """
**Git-like Commands:**
`DuDe stagefile .` - Stage all files in coldleads folder
`DuDe stagefile file1.json file2.json` - Stage specific files
`DuDe unstagefile .` - Unstage all files
`DuDe unstagefile file1.json file2.json` - Unstage specific files
`DuDe liststaged` - List all currently staged files
`DuDe commit message="Your commit message"` - Commit staged files with a message
`DuDe help_git` - Show this help message

**Examples:**
`DuDe stagefile .` - Stage all files
`DuDe stagefile company_name` - Stage files containing "company_name"
`DuDe unstagefile company_name` - Unstage files containing "company_name"
`DuDe commit message="Add new leads for marketing campaign"`
    """
    await ctx.send(help_text)

@bot.command(name='runemailcrew')
async def run_email_crew(ctx):
    """Runs the Email automation multi AI agent crew to process leads in the businesses.json file."""
    try:
        # Check if there are any leads in the businesses.json file
        with open(JSON_FILE, 'r') as f:
            businesses = json.load(f)
        
        if not businesses:
            await ctx.send("No leads found in the database. Please add leads first using the `addlead` command.")
            return
        
        await ctx.send(f"Starting Email automation for {len(businesses)} leads. This may take some time...")
        
        # Create a thread to run the email automation to avoid blocking the bot
        def run_email_automation():
            try:
                run()
                # Send a follow-up message when done
                asyncio.run_coroutine_threadsafe(
                    ctx.send("Email automation completed successfully!"), 
                    bot.loop
                )
            except Exception as e:
                # Send error message if something goes wrong
                error_message = f"Error during email automation: {str(e)}"
                asyncio.run_coroutine_threadsafe(
                    ctx.send(error_message),
                    bot.loop
                )
        
        # Start the thread
        threading.Thread(target=run_email_automation).start()
        
    except Exception as e:
        await ctx.send(f"Error starting email automation: {str(e)}")

# Run the bot
if __name__ == '__main__':
    # Check if token is available
    if not TOKEN:
        print("Error: No Discord bot token found. Please set the DISCORD_BOT_TOKEN environment variable.")
        print("You can create a .env file with DISCORD_BOT_TOKEN=your_token_here")
        exit(1)
    
    bot.run(TOKEN) 