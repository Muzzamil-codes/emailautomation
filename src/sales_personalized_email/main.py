#!/usr/bin/env python
import sys
import json
from dotenv import load_dotenv

from .crew import SalesPersonalizedEmailCrew

# Load environment variables
load_dotenv()

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding necessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def run():
    """
    Run the crew.
    """
    # inputs = {
    #     "company": "Tea World",
    #     "industry": "Restaurant",
    #     "business_type": "Medium size business with multiple branches",
    #     "location": "Doha, Qatar",
    #     "our_product": "beautiful, brand-aligned websites built to impress and convert",
    #     "product": "beautiful, brand-aligned websites built to impress and convert",
    # }

    with open("businesses.json", "r") as f:
        data = json.load(f)
    
    while data:
        inputs = data[0]  # Get the first item
        inputs["our_product"] = "beautiful, brand-aligned websites built to impress and convert"
        inputs["product"] = "beautiful, brand-aligned websites built to impress and convert"
        
        # Pass the company name to the crew constructor
        SalesPersonalizedEmailCrew(company_name=inputs["company"]).crew().kickoff(inputs=inputs)

        # Remove the item from the list
        data.pop(0)

        # Save the updated list back to the file
        with open("businesses.json", "w") as f:
            json.dump(data, f, indent=4)



def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "company": "Al Maha Insurance",
        "industry": "Insurance company",
        "business_type": "Insruance brokage",
        "location": "Doha, Qatar",
        "our_product": "beautiful, brand-aligned websites built to impress and convert",
        "product": "beautiful, brand-aligned websites built to impress and convert",
    }
    try:
        # Pass the company name to the crew constructor
        SalesPersonalizedEmailCrew(company_name=inputs["company"]).crew().train(
            n_iterations=int(sys.argv[2]),
            filename=sys.argv[3],
            inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        SalesPersonalizedEmailCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "company": "Al Afaq Insurance Brokers",
        "industry": "Insurance Brokage Providers",
        "business_type": "Insurance Brokers",
        "location": "Dubai, UAE",
        # "estimated_size": "5-10 employees",
        "our_product": "beautiful, brand-aligned websites built to impress and convert",
        "product": "beautiful, brand-aligned websites built to impress and convert",
    }
    try:
        # Note: Using the model specified in the environment variables
        # Pass the company name to the crew constructor
        SalesPersonalizedEmailCrew(company_name=inputs["company"]).crew().test(
            n_iterations=int(sys.argv[1]), inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "run":
            run()
        elif sys.argv[1] == "test" and len(sys.argv) > 2:
            test()
        elif sys.argv[1] == "train" and len(sys.argv) > 3:
            train()
        elif sys.argv[1] == "replay" and len(sys.argv) > 2:
            replay()
    else:
        run()
