import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=API_KEY)


def getRespose(Query: str) -> str:
    """
    Refines the user's raw query into a clear, specific instruction
    that the orchestrator uses to select the correct tool.

    Examples:
      "how many leeve days do i have"
      → "Retrieve the annual leave entitlement policy for employees"

      "my laptoop is not wrking"
      → "Troubleshoot a laptop hardware issue for an employee"

      "who is ceo of hexaware"
      → "Find the name and details of Hexaware's CEO"
    """

    print("\n" + " Model Query Refinement ".center(40, "-"))

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are a query refinement assistant for a corporate HR/IT/Finance chatbot.

Your ONLY job is to rephrase the user's input into a clear, concise, and specific search instruction.
This refined instruction will be used to search a knowledge base — it must be specific and searchable.

Rules:
- Fix spelling mistakes and typos in the query
- Keep the intent exactly the same — do not change what the user is asking
- Make it a clear instruction or search phrase (not a question)
- Keep it under 20 words
- Do NOT answer the query
- Do NOT add extra context or explanation
- Output ONLY the refined instruction, nothing else

Examples:
User: "how many leeve days do i have"
Output: retrieve employee annual leave entitlement days balance policy

User: "my laptoop is nt wrking"
Output: troubleshoot laptop not working hardware issue

User: "wen is salaary credited"
Output: salary payment date payroll credit schedule

User: "who is ceo of hexawre"
Output: Hexaware CEO name executive director leadership

User: "how do i connct to vpn"
Output: VPN connection setup guide steps"""
                },
                {
                    "role": "user",
                    "content": f"User query: {Query}"
                }
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=60,        # refined query should be short
            temperature=0.1,      # low temperature = consistent output
        )

        refined = chat_completion.choices[0].message.content.strip()

        print(f"Original : {Query}")
        print(f"Refined  : {refined}")
        print("-" * 40)

        return refined

    except Exception as e:
        print(f"Model refinement error: {e}")
        # Fall back to original query if refinement fails
        return Query