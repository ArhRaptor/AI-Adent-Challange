from google import genai

client = genai.Client()

while True:
    prompt = input("\nВы: ")

    if prompt.lower() == "exit":
        print("До свидания!")
        break

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    print("\nGemini:", response.text)