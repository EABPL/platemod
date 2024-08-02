from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os
import json

client = OpenAI()

assistant = client.beta.assistants.retrieve("asst_urLwyiLLsPp1QPSMxjBY4UAE")

router = APIRouter()

class Tag(BaseModel):
    tag: str
    summary: str
    confidence: int

class PlateResult(BaseModel):
    plate: str
    tags: list[str]
    reason: str

class CheckResponse(BaseModel):
    data: list[PlateResult]

class PlateModRequest(BaseModel):
    plates: list

async def get_chatgpt_response(plates: list) -> list[PlateResult]:

    thread = client.beta.threads.create()

    content = json.dumps({"plates": plates})

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=content
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions=assistant.instructions + " Always reverse the content to check the inverse content. Ensure the score is added to the response. Ensure reverse-content check is performed. Respond in JSON format with fields: plate, tags, reason."
    )

    if run.status == 'completed':
        messages = list(client.beta.threads.messages.list(thread_id=thread.id))
        last_message = messages[0]
        last_message_content = last_message.content[0].text.value

        try:
            response_json = json.loads(last_message_content)
            print(f"Response JSON: {response_json}")  # Add debugging print statement

            # Ensure the tags are parsed correctly
            results = []
            for result in response_json["data"]:
                tags = result["tags"]
                reason = result.get("reason", "")
                results.append(PlateResult(plate=result["plate"], tags=tags, reason=reason))
            return results
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing response: {e}")
            raise HTTPException(status_code=500, detail="Failed to decode JSON response from ChatGPT")
    else:
        raise HTTPException(status_code=500, detail=f"Run status: {run.status}")

@router.post("/check", response_model=CheckResponse)
async def check_content(request: PlateModRequest):
    response = await get_chatgpt_response(request.plates)
    return CheckResponse(data=response)
