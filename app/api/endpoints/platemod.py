from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from .training import system_instructions

import os
import json

client = OpenAI()

assistant = client.beta.assistants.retrieve("asst_urLwyiLLsPp1QPSMxjBY4UAE")

router = APIRouter()

class PartResult(BaseModel):
    part: str
    tags: list[str]
    reason: str
    confidence_rating: int

class PlateResult(BaseModel):
    plate: str
    parts: list[PartResult]

class CheckResponse(BaseModel):
    data: list[PlateResult]

class PlateModRequest(BaseModel):
    plates: list


async def get_chatgpt_response(plates: list[str]) -> list[PlateResult]:
    # Prepare the content for the chat completion request
    content = {
        "plates": plates
    }
    messages = [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": json.dumps(content)}
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.2,
        max_tokens=4095,
        top_p=0.4,
        frequency_penalty=0,
        presence_penalty=0
    )
        
    if response.choices:
        last_message_content = response.choices[0].message.content
        try:
            response_json = json.loads(last_message_content)

            # Ensure the tags are parsed correctly
            results = []
            for result in response_json["data"]:
                parts = []
                for part in result["parts"]:
                    part_name = part.get("part", "")
                    tags = part.get("tags", [])
                    reason = part.get("reason", "")
                    rating = part.get("confidence_rating", 0)
                    parts.append(PartResult(part=part_name, tags=tags, reason=reason, confidence_rating=rating))
                results.append(PlateResult(plate=result["plate"], parts=parts))
            return results
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Error parsing response: {e}")
            raise HTTPException(status_code=500, detail="Failed to decode JSON response from ChatGPT")
    else:
        raise HTTPException(status_code=500, detail="No response from ChatGPT")

async def get_assistant_response(plates: list) -> list[PlateResult]:

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
        instructions=system_instructions
    )

    if run.status == 'completed':
        messages = list(client.beta.threads.messages.list(thread_id=thread.id))
        last_message = messages[0]
        last_message_content = last_message.content[0].text.value

        try:
            response_json = json.loads(last_message_content)
            print(response_json["data"])

            # Ensure the tags are parsed correctly
            results = []
            for result in response_json["data"]:
                parts = []
                for part in result["parts"]:
                    part_name = part.get("part", "")
                    tags = part.get("tags", [])
                    reason = part.get("reason", "")
                    rating = part.get("confidence_rating", 0)
                    print(part_name, tags, reason, rating)
                    parts.append(PartResult(part=part_name, tags=tags, reason=reason, confidence_rating=rating))
                results.append(PlateResult(plate=result["plate"], parts=parts))
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
