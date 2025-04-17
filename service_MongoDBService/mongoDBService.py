import asyncio
from fastapi import FastAPI, Response, Request, HTTPException
import uvicorn
import json
from datetime import datetime
import uuid

import asyncio
import aio_pika


import sys
import os

# Import necessary MongoDB modules
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import DuplicateKeyError

from pydantic import ValidationError

sys.path.append(os.path.join(os.path.dirname(__file__), "../ServiceTemplates/Basic"))


from HTTP_SERVER import HTTPServer
from MESSAGE_QUEUE import MessageQueue


class Service():
    def __init__(self,httpServerHost, httpServerPort):
        self.messageQueue = MessageQueue("amqp://guest:guest@localhost/","/")
        self.httpServer = HTTPServer(httpServerHost, httpServerPort)
        
        # MongoDB Configuration
        self.mongo_client = MongoClient('mongodb://localhost:27017/', server_api=ServerApi('1'))
        self.db = self.mongo_client["ES"]  # Database name from MongoSchema.json
        self.event_collection = self.db["EVENTS"]  # Collection name from MongoSchema.json
        self.user_profile_collection = self.db["USER_PROFILE"] # Collection name from MongoSchema.json
        self.mentor_profile_collection = self.db["MENTOR_PROFILE"] # Collection name from MongoSchema.json
        self.teams_collection = self.db["TEAMS"]
        self.milestones_collection = self.db["MILESTONES"]
        
    def validate_event_data(self, event_data):
        """Validate event data against the required schema"""
        required_fields = [
            "CONTACT_INFO", "DESCRIPTION", "EVENT_DATE", "EVENT_NAME",
             "REGISTRATION_DEADLINE", "VENUE", "ELIGIBILITY"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in event_data:
                return False, f"Missing required field: {field}"
        
        # Validate CONTACT_INFO
        if not isinstance(event_data["CONTACT_INFO"], dict):
            return False, "CONTACT_INFO must be an object"
        
        if "EMAIL" not in event_data["CONTACT_INFO"] or "MOBILE_NUMBER" not in event_data["CONTACT_INFO"]:
            return False, "CONTACT_INFO must contain EMAIL and MOBILE_NUMBER"
            
        # Validate dates (convert string dates to datetime objects)
        try:
            if isinstance(event_data["EVENT_DATE"], str):
                event_data["EVENT_DATE"] = datetime.fromisoformat(event_data["EVENT_DATE"].replace('Z', '+00:00'))
            
            if isinstance(event_data["REGISTRATION_DEADLINE"], str):
                event_data["REGISTRATION_DEADLINE"] = datetime.fromisoformat(event_data["REGISTRATION_DEADLINE"].replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            
        # Validate ELIGIBILITY
        if not isinstance(event_data["ELIGIBILITY"], list):
            return False, "ELIGIBILITY must be an array of strings"
            
        return True, "Valid data"

    def validate_milestone_data(self, milestone_data):
        """Validate milestone data against the schema"""
        required_fields = ["NAME", "DEADLINE", "STATUS"]
        for field in required_fields:
            if field not in milestone_data:
                return False, f"Missing required field: {field}"

        # Validate STATUS enum
        valid_statuses = ["Not Started", "In Progress", "Completed"]
        if milestone_data["STATUS"] not in valid_statuses:
            return False, f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

        # Validate DEADLINE format
        try:
            if isinstance(milestone_data["DEADLINE"], str):
                datetime.fromisoformat(milestone_data["DEADLINE"].replace('Z', '+00:00'))
        except ValueError:
            return False, "Invalid date format for DEADLINE. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"

        return True, "Valid data"

    def parse_date_time(self,field):
        if isinstance(field, dict) and "$date" in field:
            return datetime.fromisoformat(field["$date"].replace("Z", "+00:00"))
        return field



    async def get_all_events_organized_by_user(self, userID, mongoProjecton=None):
        if mongoProjecton == None:
            return self.event_collection.find({"ORGANIZER": userID}, {'_id': 0})
        
        return self.event_collection.find({"ORGANIZER": userID}, mongoProjecton)

    async def get_all_teams_for_a_user(self, userID, mongoProjecton=None):
        if mongoProjecton == None:
            return self.teams_collection.find(
                {"PARTICIPANTS": {"$elemMatch": {"USER_ID": userID}}},
                {'_id': 0}
            )
        
        return self.teams_collection.find(
                {"PARTICIPANTS": {"$elemMatch": {"USER_ID": userID}}},
                mongoProjecton
            )



    async def ConfigureAPIRoutes(self):

    # Events ---------------------------------

        @self.httpServer.app.get("/Events/AllEvents")
        async def get_all_event():
            print("Fetching All Events")
            events = list(self.event_collection.find({}, {'_id': 0}))  # Fetch all events, exclude _id
            return {"EVENTS": events}
    
        @self.httpServer.app.get("/Events/Organized/User/AllEvents")
        async def get_all_organized_events(
            USER_ID: str,
            request: Request
        ):
            print(f"Fetching All Events Organized by User: {USER_ID}")
            if not USER_ID:
                raise HTTPException(status_code=400, detail="USER_ID is required")

            # Query the database for events organized by the user
            # events = list(self.event_collection.find({"ORGANIZER": USER_ID}, {'_id': 0}))
            events = list(await self.get_all_events_organized_by_user(USER_ID, {'_id': 0}))

            if not events:
                # It's okay if a user hasn't organized any events, return an empty list
                return {"EVENTS": []}

            return {"EVENTS": events}

        @self.httpServer.app.get("/Events/GetEventInfo")
        async def get_event_info(
            EVENT_ID : str,
        ):
            # Check if EVENT_ID is provided
            if not EVENT_ID:
                raise HTTPException(status_code=400, detail="EVENT_ID is required")
            
            # Fetch event details from the database
            event = self.event_collection.find_one({"EVENT_ID": EVENT_ID}, {'_id': 0})
            if not event:
                raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} not found")
            
            # Return the event details
            return {"EVENT_INFO": event}

        @self.httpServer.app.post("/Events/CreateNewEvent")
        async def insert_event(request: Request):
            try:
                event_data = await request.json()
                print("Received event data:", event_data)
                
                # Validate event data
                is_valid, message = self.validate_event_data(event_data)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=message)
                
                # Generate a unique EVENT_ID
                event_data["EVENT_ID"] = str(uuid.uuid4())

                event_data["QUESTIONNAIRE"] = []
                
                # Add creation timestamp
                event_data["CREATED_AT"] = datetime.now()

                event_data["EVENT_DATE"] = self.parse_date_time(event_data.get("EVENT_DATE"))
                event_data["REGISTRATION_DEADLINE"] = self.parse_date_time(event_data.get("REGISTRATION_DEADLINE"))


                print(event_data)
                
                # Insert the event
                result = self.event_collection.insert_one(event_data)
                
                return {"message": "Event inserted successfully", "EVENT_ID": event_data["EVENT_ID"]}
            except HTTPException as e:
                raise e
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="An event with this ID already exists")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error inserting event: {str(e)}")
            
        @self.httpServer.app.put("/Events/Update")
        async def update_event(request: Request):
            try:
                event_data = await request.json()
                print("Updating Event", event_data)
                
                # Check if EVENT_ID is provided
                if "EVENT_ID" not in event_data:
                    raise HTTPException(status_code=400, detail="EVENT_ID is required for updates")
                
                # Check if the event exists
                existing_event = self.event_collection.find_one({"EVENT_ID": event_data["EVENT_ID"]})
                if not existing_event:
                    raise HTTPException(status_code=404, detail=f"Event with ID {event_data['EVENT_ID']} not found")
                
                # Validate event data
                is_valid, message = self.validate_event_data(event_data)
                if not is_valid:
                    raise HTTPException(status_code=400, detail=message)
                
                # Update the event
                result = self.event_collection.update_one(
                    {"EVENT_ID": event_data["EVENT_ID"]}, 
                    {"$set": event_data}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the event"}
                    
                return {"message": "Event updated successfully"}
            except HTTPException as e:
                raise e
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")
    
        @self.httpServer.app.put("/Events/Update/EventBanner")
        async def update_event_banner(
            request: Request
        ):
            data = await request.json()

            EVENT_ID = data.get("EVENT_ID")
            EVENT_BANNER = data.get("EVENT_BANNER")

            # Check if EVENT_ID is provided
            if not EVENT_ID:
                raise HTTPException(status_code=400, detail="EVENT_ID is required")
            
            # Check if EVENT_BANNER is provided
            if not EVENT_BANNER:
                raise HTTPException(status_code=400, detail="EVENT_BANNER is required")
            
            # Check if the event exists
            existing_event = self.event_collection.find_one({"EVENT_ID": EVENT_ID})
            if not existing_event:
                raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} not found")
            
            # Update the event
            result = self.event_collection.update_one(
                {"EVENT_ID": EVENT_ID},
                {"$set": {"IMAGE": EVENT_BANNER}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the event"}
            
            return {"message": "Event banner updated successfully"}

        @self.httpServer.app.delete("/Events/DeleteEvent")
        async def delete_event(
            EVENT_ID: str,
        ):
            # Check if EVENT_ID is provided
            if not EVENT_ID:
                raise HTTPException(status_code=400, detail="EVENT_ID is required")

            # Check if the event exists
            existing_event = self.event_collection.find_one({"EVENT_ID": EVENT_ID})
            if not existing_event:
                raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} not found")

            try:
                # Delete the event
                result = self.event_collection.delete_one({"EVENT_ID": EVENT_ID})

                if result.deleted_count == 0:
                    # This case should ideally not happen if find_one succeeded, but good practice to check
                    raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} could not be deleted")

                return {"message": f"Event with ID {EVENT_ID} deleted successfully"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")


        @self.httpServer.app.post("/Events/Discussion/AddNewQuestion")
        async def add_new_question(
            request: Request # Use request body for POST
        ):
            try:
                data = await request.json()
                EVENT_ID = data.get("EVENT_ID")
                QUESTION = data.get("QUESTION")

                # Check if EVENT_ID and QUESTION are provided
                if not EVENT_ID:
                    raise HTTPException(status_code=400, detail="EVENT_ID is required")
                if not QUESTION:
                    raise HTTPException(status_code=400, detail="QUESTION is required")

                # Check if the event exists
                existing_event = self.event_collection.find_one({"EVENT_ID": EVENT_ID})
                if not existing_event:
                    raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} not found")

                # Create the new question object
                new_question = {
                    "ID": str(uuid.uuid4()), # Generate a unique ID for the question
                    "QUESTION": QUESTION,
                    "ANSWER": None # Initialize answer as null or empty
                }

                # Add the new question to the QUESTIONNAIRE array
                result = self.event_collection.update_one(
                    {"EVENT_ID": EVENT_ID},
                    {"$push": {"QUESTIONNAIRE": new_question}}
                )

                if result.modified_count == 0:
                    raise HTTPException(status_code=500, detail="Failed to add question to the event")

                return {"message": "Question added successfully", "QUESTION_ID": new_question["ID"]}

            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error adding question: {str(e)}")


        @self.httpServer.app.get("/Events/Organizer/GetEventInfo")
        async def get_organizer_specific_event_info(
            EVENT_ID: str,
        ):
            # Check if EVENT_ID is provided
            if not EVENT_ID:
                raise HTTPException(status_code=400, detail="EVENT_ID is required")

            # Fetch event details from the database, excluding the internal _id
            # Assuming organizer-specific info means the full event document for now
            event = self.event_collection.find_one({"EVENT_ID": EVENT_ID}, {'_id': 0})

            if not event:
                raise HTTPException(status_code=404, detail=f"Event with ID {EVENT_ID} not found")

            # Return the event details
            # Potentially, you could add more checks here to ensure the requester is the actual organizer
            # before returning sensitive data if the schema evolves.
            return {"EVENT_INFO": event}



    # User Profile -------------------------
        
        @self.httpServer.app.get("/UserProfile/GetUserProfile")
        async def get_user_profile(
            USER_ID: str, 
            request: Request
        ):
            # Check if userID is provided
            if not USER_ID:
                raise HTTPException(status_code=400, detail="userID is required")
            
            # Fetch user profile from the database
            user_profile = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID}, {'_id': 0})
            if not user_profile:
                raise HTTPException(status_code=404, detail=f"User profile with ID {userID} not found")
            
            # Return the user profile
            return {"USER_PROFILE": user_profile}
        
        @self.httpServer.app.get("/UserProfile/GetAllUserProfiles")
        async def get_all_user_profiles():
            print("Fetching All User Profiles")
            user_profiles = list(self.db["USER_PROFILE"].find({}, {'_id': 0}))
            return {"USER_PROFILES": user_profiles}


        @self.httpServer.app.post("/UserProfile/CreateNewUser")
        async def insert_new_user(
            request: Request
        ):
            try:
                
                user_data = await request.json()
                print("Received user data:", user_data)
                
                # Generate a unique USER_ID
                user_data["USER_ID"] = str(uuid.uuid4())

                user_data["PLATFORM_STATUS"] = "ACTIVE"
                
                # Add creation timestamp
                user_data["CREATED_AT"] = datetime.now()

                user_data["HISTORY"] = []

                user_data["GAME_RELATED_INFO"] = {}
                

                # Insert the user profile
                result = self.db["USER_PROFILE"].insert_one(user_data)
                
                return {"message": "User profile inserted successfully", "USER_ID": user_data["USER_ID"]}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="A user with this ID already exists")
            except Exception as e:
                print(str(e))
                raise HTTPException(status_code=500, detail=f"Error inserting user profile: {str(e)}")

        @self.httpServer.app.put("/UserProfile/Update/ProfilePic")
        async def update_user_profile_pic(
            request: Request
        ):
            data = await request.json()

            USER_ID = data.get("USER_ID")
            PROFILE_PIC = data.get("PROFILE_PIC")

            # Check if USER_ID is provided
            if not USER_ID:
                raise HTTPException(status_code=400, detail="USER_ID is required")
            
            # Check if PROFILE_PIC is provided
            if not PROFILE_PIC:
                raise HTTPException(status_code=400, detail="PROFILE_PIC is required")
            
            # Check if the user profile exists
            existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
            if not existing_user:
                raise HTTPException(status_code=404, detail=f"User with ID {USER_ID} not found")
            
            # Update the user profile
            result = self.db["USER_PROFILE"].update_one(
                {"USER_ID": USER_ID},
                {"$set": {"PROFILE_PIC": PROFILE_PIC}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the user profile"}
            
            return {"message": "User profile updated successfully"}

        @self.httpServer.app.put("/UserProfile/Update/ProfileBanner")
        async def update_user_profile_banner(
            request: Request
        ):
            data = await request.json()

            USER_ID = data.get("USER_ID")
            PROFILE_BANNER = data.get("PROFILE_BANNER")

            # Check if USER_ID is provided
            if not USER_ID:
                raise HTTPException(status_code=400, detail="USER_ID is required")
            
            # Check if PROFILE_BANNER is provided
            if not PROFILE_BANNER:
                raise HTTPException(status_code=400, detail="PROFILE_BANNER is required")
            
            # Check if the user profile exists
            existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
            if not existing_user:
                raise HTTPException(status_code=404, detail=f"User with ID {USER_ID} not found")
            
            # Update the user profile
            result = self.db["USER_PROFILE"].update_one(
                {"USER_ID": USER_ID},
                {"$set": {"PROFILE_BANNER": PROFILE_BANNER}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the user profile"}
            
            return {"message": "User profile updated successfully"}





    # Mentor Profile -------------------------

        @self.httpServer.app.get("/MentorProfile/GetMentorProfile")
        async def get_mentor_profile(
            MENTOR_ID: str,
            request: Request
        ):
            # Check if mentorID is provided
            if not MENTOR_ID:
                raise HTTPException(status_code=400, detail="mentorID is required")

            # Fetch mentor profile from the database
            mentor_profile = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID}, {'_id': 0})
            if not mentor_profile:
                raise HTTPException(status_code=404, detail=f"Mentor profile with ID {mentorID} not found")

            # Return the mentor profile
            return {"MENTOR_PROFILE": mentor_profile}

        @self.httpServer.app.get("/MentorProfile/GetAllMentorProfiles")
        async def get_all_mentor_profiles():
            print("Fetching All Mentor Profiles")
            mentor_profiles = list(self.mentor_profile_collection.find({}, {'_id': 0}))
            return {"MENTOR_PROFILES": mentor_profiles}

        @self.httpServer.app.get("/MentorProfile/Dashboard/GetMentorProfile")
        async def get_mentor_profile_for_dashboard(
            MENTOR_ID: str,
            request: Request
        ):
            # Check if mentorID is provided
            if not MENTOR_ID:
                raise HTTPException(status_code=400, detail="MENTOR_ID is required")

            # Define the projection to fetch only the required fields for the dashboard
            projection = {
                "_id": 0,  # Exclude the default MongoDB ID
                "PROFILE_PIC": 1,
                "TAGLINE": 1,
                "USER_NAME": 1,
                "RATING": 1,
                "VERIFIED": 1,
                "SESSIONS_COMPLETED": 1
            }

            # Fetch mentor profile from the database with the specified projection
            mentor_profile = self.mentor_profile_collection.find_one(
                {"MENTOR_ID": MENTOR_ID},
                projection
            )

            if not mentor_profile:
                raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

            # Return the mentor profile dashboard data
            return {"MENTOR_PROFILE_DASHBOARD": mentor_profile}

        @self.httpServer.app.post("/MentorProfile/CreateNewMentor")
        async def insert_new_mentor(request: Request):
            try:
                mentor_data = await request.json()
                print("Received mentor data:", mentor_data)

                # Generate a unique MENTOR_ID
                mentor_data["MENTOR_ID"] = str(uuid.uuid4())

                # Add creation timestamp
                mentor_data["CREATED_AT"] = datetime.now() 

                # Set default values for optional fields
                mentor_data["RATING"] = 3.0

                # Insert the mentor profile
                result = self.mentor_profile_collection.insert_one(mentor_data)

                return {"message": "Mentor profile inserted successfully", "MENTOR_ID": mentor_data["MENTOR_ID"]}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="A mentor with this ID already exists")
            except Exception as e:
                print(str(e))
                raise HTTPException(status_code=500, detail=f"Error inserting mentor profile: {str(e)}")
       
        @self.httpServer.app.put("/MentorProfile/Update/ProfilePic")
        async def update_mentor_profile_pic(
            request: Request
        ):
            data = await request.json()

            MENTOR_ID = data.get("MENTOR_ID")
            PROFILE_PIC = data.get("PROFILE_PIC")

            # Check if MENTOR_ID is provided
            if not MENTOR_ID:
                raise HTTPException(status_code=400, detail="MENTOR_ID is required")
            
            # Check if PROFILE_PIC is provided
            if not PROFILE_PIC:
                raise HTTPException(status_code=400, detail="PROFILE_PIC is required")
            
            # Check if the mentor profile exists
            existing_mentor = self.db["MENTOR_PROFILE"].find_one({"MENTOR_ID": MENTOR_ID})
            if not existing_mentor:
                raise HTTPException(status_code=404, detail=f"Mentor with ID {MENTOR_ID} not found")
            
            # Update the mentor profile
            result = self.db["MENTOR_PROFILE"].update_one(
                {"MENTOR_ID": MENTOR_ID},
                {"$set": {"PROFILE_PIC": PROFILE_PIC}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the mentor profile"}
            
            return {"message": "Mentor profile pic updated successfully"}

        @self.httpServer.app.put("/MentorProfile/Update/ProfileBanner")
        async def update_mentor_profile_banner(
            request: Request
        ):
            data = await request.json()

            MENTOR_ID = data.get("MENTOR_ID")
            PROFILE_BANNER = data.get("PROFILE_BANNER")

            # Check if MENTOR_ID is provided
            if not MENTOR_ID:
                raise HTTPException(status_code=400, detail="MENTOR_ID is required")
            
            # Check if PROFILE_BANNER is provided
            if not PROFILE_BANNER:
                raise HTTPException(status_code=400, detail="PROFILE_BANNER is required")
            
            # Check if the mentor profile exists
            existing_mentor = self.db["MENTOR_PROFILE"].find_one({"MENTOR_ID": MENTOR_ID})
            if not existing_mentor:
                raise HTTPException(status_code=404, detail=f"Mentor with ID {MENTOR_ID} not found")
            
            # Update the mentor profile
            result = self.db["MENTOR_PROFILE"].update_one(
                {"MENTOR_ID": MENTOR_ID},
                {"$set": {"PROFILE_BANNER": PROFILE_BANNER}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the mentor profile"}
            
            return {"message": "Mentor profile banner updated successfully"}





    # Teams -----------------------------------

        @self.httpServer.app.get("/Teams/User/GetAllTeams")
        async def get_all_teams_for_a_user(
            USER_ID: str,
            request: Request
        ):
            print(f"Fetching All Teams for User: {USER_ID}")
            if not USER_ID:
                raise HTTPException(status_code=400, detail="USER_ID is required")

            # Query the database for teams where the user is a participant
            # We use $elemMatch to find documents where the PARTICIPANTS array contains at least one element matching the criteria
            # teams = list(self.teams_collection.find(
            #     {"PARTICIPANTS": {"$elemMatch": {"USER_ID": USER_ID}}},
            #     {'_id': 0}
            # ))

            teams = list(await self.get_all_teams_for_a_user(USER_ID, {'_id': 0}))

            if not teams:
                # It's okay if a user isn't part of any teams, return an empty list
                return {"TEAMS": []}

            return {"TEAMS": teams}

        @self.httpServer.app.post("/Teams/CreateNewTeam")
        async def insert_new_team(request: Request):
            try:
                team_data = await request.json()
                print("Received mentor data:", team_data)
                
                # Parse milestone dates if present and in the unsupported format
                if "MILESTONES" in team_data:
                    for milestone in team_data["MILESTONES"]:
                        if isinstance(milestone.get("MILESTONE_DATE"), dict) and "$date" in milestone["MILESTONE_DATE"]:
                            milestone["MILESTONE_DATE"] = datetime.fromisoformat(milestone["MILESTONE_DATE"]["$date"].replace("Z", "+00:00"))

                team_data["TEAM_ID"] = str(uuid.uuid4())

                # Add creation timestamp
                team_data["CREATED_AT"] = datetime.now() 

                team_data["EVENTS_ENROLLED"] = []

                result = self.teams_collection.insert_one(team_data)

                return {"message": "Team profile inserted successfully", "TEAM_ID": team_data["TEAM_ID"]}

            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="A mentor with this ID already exists")
            except Exception as e:
                print(str(e))
                raise HTTPException(status_code=500, detail=f"Error inserting team profile: {str(e)}")
       
        @self.httpServer.app.put("/Teams/Update/TeamLogo")
        async def update_team_logo(
            request: Request
        ):
            data = await request.json()

            TEAM_ID = data.get("TEAM_ID")
            TEAM_LOGO = data.get("TEAM_LOGO")

            # Check if USER_ID is provided
            if not TEAM_ID:
                raise HTTPException(status_code=400, detail="USER_ID is required")
            
            # Check if PROFILE_PIC is provided
            if not TEAM_LOGO:
                raise HTTPException(status_code=400, detail="PROFILE_PIC is required")
            
            # Check if the user profile exists
            existing_user = self.db["TEAMS"].find_one({"TEAM_ID": TEAM_ID})
            if not existing_user:
                raise HTTPException(status_code=404, detail=f"User with ID {TEAM_ID} not found")
            
            # Update the user profile
            result = self.db["TEAMS"].update_one(
                {"TEAM_ID": TEAM_ID},
                {"$set": {"TEAM_LOGO": TEAM_LOGO}}
            )
            
            if result.modified_count == 0:
                return {"message": "No changes were made to the user profile"}
            
            return {"message": "Team logo updated successfully"}

        @self.httpServer.app.delete("/Teams/DisbandTeam")
        async def disband_team(
            TEAM_ID: str,
            request: Request
        ):
            # Check if TEAM_ID is provided
            if not TEAM_ID:
                raise HTTPException(status_code=400, detail="TEAM_ID is required")
            
            # Check if the team exists
            existing_team = self.teams_collection.find_one({"TEAM_ID": TEAM_ID})
            if not existing_team:
                raise HTTPException(status_code=404, detail=f"Team with ID {TEAM_ID} not found")
            
            # Delete the team
            result = self.teams_collection.delete_one({"TEAM_ID": TEAM_ID})
            
            if result.deleted_count == 0:
                return {"message": "No changes were made to the team"}
            
            return {"message": "Team disbanded successfully"}

        @self.httpServer.app.get("/Teams/GetTeamInfo")
        async def get_single_team_info(
            TEAM_ID: str,
            request: Request
        ):
            print(f"Fetching Team Info for TEAM_ID: {TEAM_ID}")
            # Check if TEAM_ID is provided
            if not TEAM_ID:
                raise HTTPException(status_code=400, detail="TEAM_ID is required")

                # Query the database for the team with the specified TEAM_ID
                # Exclude the MongoDB internal _id field
                team_info = self.teams_collection.find_one(
                {"TEAM_ID": TEAM_ID},
                {'_id': 0}
                )

                # Check if a team was found
                if not team_info:
                    raise HTTPException(status_code=404, detail=f"Team with ID {TEAM_ID} not found")

            # Return the team information
                return {"TEAM_INFO": team_info}
            

    # Milestones

        @self.httpServer.app.post("/Milestone/CreateNewMilestone")
        async def create_milestone(
            PERSONA: str,
            ID: str,
            request: Request
        ):
            if not PERSONA or not ID:
                raise HTTPException(status_code=400, detail="PERSONA and ID are required")

            milestone_data = await request.json()
            
            # Validate milestone data
            is_valid, message = self.validate_milestone_data(milestone_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)

            # Generate milestone ID
            milestone_id = str(uuid.uuid4())
            
            milestone_doc = {
                "PERSONA": PERSONA,
                "ID": ID,
                "NAME": milestone_data["NAME"],
                "DEADLINE": datetime.fromisoformat(milestone_data["DEADLINE"].replace('Z', '+00:00')),
                "STATUS": milestone_data["STATUS"],
                "MILESTONE_ID": milestone_id
            }

            try:
                result = self.db["MILESTONES"].insert_one(milestone_doc)
                return {"message": "Milestone created successfully", "MILESTONE_ID": milestone_id}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.httpServer.app.get("/Milestone/GetMilestoneInfo")
        async def get_milestone_info(
            PERSONA: str,
            ID: str,
            MILESTONE_ID: str
        ):
            if not all([PERSONA, ID, MILESTONE_ID]):
                raise HTTPException(status_code=400, detail="PERSONA, ID and MILESTONE_ID are required")

            milestone = self.db["MILESTONES"].find_one(
                {"PERSONA": PERSONA, "ID": ID, "MILESTONE_ID": MILESTONE_ID},
                {"_id": 0}
            )

            if not milestone:
                raise HTTPException(status_code=404, detail="Milestone not found")

            # Convert datetime to ISO format for JSON response
            if isinstance(milestone.get("DEADLINE"), datetime):
                milestone["DEADLINE"] = milestone["DEADLINE"].isoformat() + "Z"

            return {"MILESTONE_INFO": milestone}

        @self.httpServer.app.put("/Milestone/UpdateMilestone")
        async def update_milestone(
            PERSONA: str,
            ID: str,
            MILESTONE_ID: str,
            request: Request
        ):
            if not all([PERSONA, ID, MILESTONE_ID]):
                raise HTTPException(status_code=400, detail="PERSONA, ID and MILESTONE_ID are required")

            update_data = await request.json()
            
            # Validate update data
            is_valid, message = self.validate_milestone_data(update_data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=message)

            # Convert deadline to datetime
            if "DEADLINE" in update_data:
                update_data["DEADLINE"] = datetime.fromisoformat(update_data["DEADLINE"].replace('Z', '+00:00'))

            result = self.db["MILESTONES"].update_one(
                {"PERSONA": PERSONA, "ID": ID, "MILESTONE_ID": MILESTONE_ID},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Milestone not found")

            return {"message": "Milestone updated successfully"}

        @self.httpServer.app.delete("/Milestone/DeleteMilestone")
        async def delete_milestone(
            PERSONA: str,
            ID: str,
            MILESTONE_ID: str
        ):
            if not all([PERSONA, ID, MILESTONE_ID]):
                raise HTTPException(status_code=400, detail="PERSONA, ID and MILESTONE_ID are required")

            result = self.db["MILESTONES"].delete_one(
                {"PERSONA": PERSONA, "ID": ID, "MILESTONE_ID": MILESTONE_ID}
            )

            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Milestone not found")

            return {"message": "Milestone deleted successfully"}

        @self.httpServer.app.put("/Milestone/UpdateMilestoneStatus")
        async def update_milestone_status(
            PERSONA: str,
            ID: str,
            MILESTONE_ID: str,
            request: Request
        ):
            if not all([PERSONA, ID, MILESTONE_ID]):
                raise HTTPException(status_code=400, detail="PERSONA, ID and MILESTONE_ID are required")

            status_data = await request.json()
            
            if "STATUS" not in status_data:
                raise HTTPException(status_code=400, detail="STATUS is required")

            valid_statuses = ["Not Started", "In Progress", "Completed"]
            if status_data["STATUS"] not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

            result = self.db["MILESTONES"].update_one(
                {"PERSONA": PERSONA, "ID": ID, "MILESTONE_ID": MILESTONE_ID},
                {"$set": {"STATUS": status_data["STATUS"]}}
            )

            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Milestone not found")

            return {"message": "Milestone status updated successfully"}

    async def startService(self):
        # await self.messageQueue.InitializeConnection()
        # await self.messageQueue.AddQueueAndMapToCallback("queue1", self.fun1)
        # await self.messageQueue.AddQueueAndMapToCallback("queue2", self.fun2)
        # await self.messageQueue.StartListeningToQueue()

        await self.ConfigureAPIRoutes()
        await self.httpServer.run_app()

        
async def start_service():
    service = Service('0.0.0.0', 14000)
    await service.startService()

if __name__ == "__main__":
    asyncio.run(start_service())
