from google import genai

client = genai.Client(api_key="your_google_gemini_api_key_here")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)
