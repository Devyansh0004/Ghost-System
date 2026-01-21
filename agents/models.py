from pydantic import BaseModel, Field
from typing import List, Optional

class Meeting(BaseModel):
    name: str = Field(description="Title or subject of the meeting")
    # CHANGED: Made link optional. Sometimes we only get an ID/Pass.
    link: Optional[str] = Field(None, description="URL link to the meeting (Zoom, Meet, Teams, etc.)")
    id: Optional[str] = Field(None, description="Meeting ID if available")
    code: Optional[str] = Field(None, description="Passcode or password if available")

class Event(BaseModel):
    name: str = Field(description="Name or title of the event")
    time: str = Field(description="Date and time of the event")
    location: Optional[str] = Field(None, description="Physical location or 'Online'")
    description: Optional[str] = Field(None, description="Brief details about the event agenda")
    link: Optional[str] = Field(None, description="URL associated with this event if found") 

class GroupScrapeResult(BaseModel):
    meetings: List[Meeting] = Field(default_factory=list, description="List of meetings found in chat")
    events: List[Event] = Field(default_factory=list, description="List of events found in chat")