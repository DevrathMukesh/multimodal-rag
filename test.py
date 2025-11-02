from google import genai

client = genai.Client(api_key="AIzaSyDD1n7Z1WAYPOt1XueQlrWaMX2lHk9TLz8")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)
