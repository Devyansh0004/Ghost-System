from pydantic import BaseModel, Field
from typing import List, Optional

class Meeting(BaseModel):
    name: str = Field(description="Title or subject of the meeting")
    link: str = Field(description="URL link to the meeting (Zoom, Meet, Teams, etc.)")
    id: Optional[str] = Field(description="Meeting ID if available")
    code: Optional[str] = Field(description="Passcode or password if available")

class Event(BaseModel):
    name: str = Field(description="Name or title of the event")
    time: str = Field(description="Date and time of the event")
    location: str = Field(description="Physical location or 'Online'")
    description: str = Field(description="Brief details about the event agenda")

class GroupScrapeResult(BaseModel):
    meetings: List[Meeting] = Field(description="List of meetings found in chat")
    events: List[Event] = Field(description="List of events found in chat")