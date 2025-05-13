from crewai_tools import ScrapeWebsiteTool, SerperDevTool
from pydantic import BaseModel
import os
import time
import re
from dotenv import load_dotenv

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

# Load environment variables
load_dotenv()

# Create a simple rate limiter for API calls
class RateLimiter:
    def __init__(self, max_calls, time_period):
        self.max_calls = max_calls
        self.time_period = time_period
        self.calls = []
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            current_time = time.time()
            # Remove calls older than the time period
            self.calls = [t for t in self.calls if current_time - t < self.time_period]
            
            # If at max calls, wait until we can make another call
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_period - (current_time - self.calls[0])
                if sleep_time > 0:
                    print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
            
            # Add this call and execute
            self.calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper

# Initialize Gemini LLM with rate limiting
class RateLimitedLLM(LLM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rate_limiter = RateLimiter(max_calls=15, time_period=60)
    
    # Override the invoke method instead of trying to wrap it in the constructor
    def invoke(self, *args, **kwargs):
        # First apply the rate limiter
        @self.rate_limiter
        def rate_limited_invoke(self, *args, **kwargs):
            # Call the parent class's invoke method
            return super(RateLimitedLLM, self).invoke(*args, **kwargs)
        
        # Call the rate-limited version
        return rate_limited_invoke(self, *args, **kwargs)

# Initialize rate-limited Gemini LLM
gemini_llm = RateLimitedLLM(
    model="gemini/gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)

class PersonalizedEmail(BaseModel):
    subject_line: str
    email_body: str
    follow_up_notes: str


@CrewBase
class SalesPersonalizedEmailCrew:
    """SalesPersonalizedEmail crew for SMEs"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    
    def __init__(self, company_name=None):
        """Initialize the crew with an optional company name"""
        self.company_name = company_name

    def get_output_filename(self):
        """Generate a filename based on company name or use default"""
        if self.company_name:
            # Create a safe filename from the company name
            safe_name = re.sub(r'[^\w\s-]', '', self.company_name).strip().lower()
            safe_name = re.sub(r'[\s-]+', '_', safe_name)
            return f"{safe_name}_personalized_email.json"
        return "sme_personalized_email.json"

    @agent
    def sme_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["sme_researcher"],
            tools=[SerperDevTool()],
            allow_delegation=False,
            verbose=True,
            llm=gemini_llm,
        )

    @agent
    def sme_email_copywriter(self) -> Agent:
        return Agent(
            config=self.agents_config["sme_email_copywriter"],
            tools=[],
            allow_delegation=False,
            verbose=True,
            llm=gemini_llm,
        )

    @task
    def research_sme_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_sme_task"],
            agent=self.sme_researcher(),
        )

    @task
    def write_sme_email_task(self) -> Task:
        # Create coldleads folder if it doesn't exist
        coldleads_folder = 'coldleads'
        if not os.path.exists(coldleads_folder):
            os.makedirs(coldleads_folder)
            
        return Task(
            config=self.tasks_config["write_sme_email_task"],
            agent=self.sme_email_copywriter(),
            output_json=PersonalizedEmail,
            output_file=os.path.join(coldleads_folder, self.get_output_filename()),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SME-focused SalesPersonalizedEmail crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            llm=gemini_llm,  # Set the default LLM for the crew
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
