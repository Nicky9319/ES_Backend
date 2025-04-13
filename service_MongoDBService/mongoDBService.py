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

    def parse_date_time(self,field):
        if isinstance(field, dict) and "$date" in field:
            return datetime.fromisoformat(field["$date"].replace("Z", "+00:00"))
        return field


    async def ConfigureAPIRoutes(self):

    # Events ---------------------------------

        @self.httpServer.app.get("/Events/AllEvents")
        async def get_event():
            print("Fetching All Events")
            events = list(self.event_collection.find({}, {'_id': 0}))  # Fetch all events, exclude _id
            return {"EVENTS": events}
    
        @self.httpServer.app.post("/Events/InsertEvent")
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
    
    
    # User Profile -------------------------
        
        @self.httpServer.app.get("/UserProfile/GetUserProfile")
        async def get_user_profile(userID: str, reuest: Request):
            # Check if userID is provided
            if not userID:
                raise HTTPException(status_code=400, detail="userID is required")
            
            # Fetch user profile from the database
            user_profile = self.db["USER_PROFILE"].find_one({"USER_ID": userID}, {'_id': 0})
            if not user_profile:
                raise HTTPException(status_code=404, detail=f"User profile with ID {userID} not found")
            
            # Return the user profile
            return {"USER_PROFILE": user_profile}
        
        @self.httpServer.app.get("/UserProfile/GetAllUserProfiles")
        async def get_all_user_profiles():
            print("Fetching All User Profiles")
            user_profiles = list(self.db["USER_PROFILE"].find({}, {'_id': 0}))
            return {"USER_PROFILES": user_profiles}

        @self.httpServer.app.post("/UserProfile/InsertNewUser")
        async def insert_new_user(request: Request):
            try:
                user_data = await request.json()
                print("Received user data:", user_data)
                
                # Generate a unique USER_ID
                user_data["USER_ID"] = str(uuid.uuid4())

                user_data["PLATFORM_STATUS"] = "ACTIVE"
                
                # Add creation timestamp
                user_data["CREATED_AT"] = datetime.now()
                

                # Insert the user profile
                result = self.db["USER_PROFILE"].insert_one(user_data)
                
                return {"message": "User profile inserted successfully", "USER_ID": user_data["USER_ID"]}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="A user with this ID already exists")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error inserting user profile: {str(e)}")

        @self.httpServer.app.put("/UserProfile/UpdateUserProfile")
        async def update_user_profile(request: Request, USER_ID : str):
            try:
                user_data = await request.json()
                print("Updating User Profile", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": user_data}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user profile"}
                    
                return {"message": "User profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

        @self.httpServer.app.put("/UserProfile/updateUserProfilePic")
        async def update_user_profile_pic(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Profile Pic", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"PROFILE_PIC": user_data.get("PROFILE_PIC")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user profile"}
                    
                return {"message": "User profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

        @self.httpServer.app.put("/UserProfile/updateUserProfileBanner")
        async def update_user_profile_banner(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Profile Banner", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"PROFILE_BANNER": user_data.get("PROFILE_BANNER")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user profile"}
                    
                return {"message": "User profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user profile: {str(e)}")

        @self.httpServer.app.put("/UserProfile/UpdateUserPlatformStatus")
        async def update_user_platform_status(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Platform Status", user_data)
                

                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                

                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"PLATFORM_STATUS": user_data.get("PLATFORM_STATUS")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user platform status"}
                    
                return {"message": "User platform status updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user platform status: {str(e)}")

        @self.httpServer.app.put("/UserProfile/UpdateUserTeamStatus")
        async def update_user_team_status(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Team Status", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"TEAM_STATUS": user_data.get("TEAM_STATUS")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user team status"}
                    
                return {"message": "User team status updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user team status: {str(e)}")

        @self.httpServer.app.put("/UserProfile/UpdateUserBio")
        async def update_user_bio(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Bio", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"BIO": user_data.get("BIO")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user bio"}
                    
                return {"message": "User bio updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user bio: {str(e)}")

        @self.httpServer.app.put("/UserProfile/UpdateUserGamesPlayed")
        async def update_user_games_played(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Games Played", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"GAMES_PLAYED": user_data.get("GAMES_PLAYED")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user games played"}
                    
                return {"message": "User games played updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user games played: {str(e)}")   

        @self.httpServer.app.put("/UserProfile/UpdateUserLocation")
        async def update_user_location(request: Request, USER_ID: str):
            try:
                user_data = await request.json()
                print("Updating User Location", user_data)
                
                # Check if the user profile exists
                existing_user = self.db["USER_PROFILE"].find_one({"USER_ID": USER_ID})
                if not existing_user:
                    raise HTTPException(status_code=404, detail=f"User profile with ID {USER_ID} not found")
                
                # Update the user profile
                result = self.db["USER_PROFILE"].update_one(
                    {"USER_ID": USER_ID}, 
                    {"$set": {"LOCATION": user_data.get("LOCATION")}}
                )
                
                if result.modified_count == 0:
                    return {"message": "No changes were made to the user location"}
                    
                return {"message": "User location updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating user location: {str(e)}")

    # Mentor Profile -------------------------

        @self.httpServer.app.get("/MentorProfile/GetMentorProfile")
        async def get_mentor_profile(mentorID: str, request: Request):
            # Check if mentorID is provided
            if not mentorID:
                raise HTTPException(status_code=400, detail="mentorID is required")

            # Fetch mentor profile from the database
            mentor_profile = self.mentor_profile_collection.find_one({"MENTOR_ID": mentorID}, {'_id': 0})
            if not mentor_profile:
                raise HTTPException(status_code=404, detail=f"Mentor profile with ID {mentorID} not found")

            # Return the mentor profile
            return {"MENTOR_PROFILE": mentor_profile}

        @self.httpServer.app.get("/MentorProfile/GetAllMentorProfiles")
        async def get_all_mentor_profiles():
            print("Fetching All Mentor Profiles")
            mentor_profiles = list(self.mentor_profile_collection.find({}, {'_id': 0}))
            return {"MENTOR_PROFILES": mentor_profiles}

        @self.httpServer.app.post("/MentorProfile/InsertNewMentor")
        async def insert_new_mentor(request: Request):
            try:
                mentor_data = await request.json()
                print("Received mentor data:", mentor_data)

                # Generate a unique MENTOR_ID
                mentor_data["MENTOR_ID"] = str(uuid.uuid4())

                # Add creation timestamp
                mentor_data["CREATED_AT"] = datetime.now() 

                # Insert the mentor profile
                result = self.mentor_profile_collection.insert_one(mentor_data)

                return {"message": "Mentor profile inserted successfully", "MENTOR_ID": mentor_data["MENTOR_ID"]}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except DuplicateKeyError:
                raise HTTPException(status_code=409, detail="A mentor with this ID already exists")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error inserting mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/UpdateMentorProfile")
        async def update_mentor_profile(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Profile", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": mentor_data}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/updateMentorProfilePic")
        async def update_mentor_profile_pic(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Profile Pic", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"PROFILE_PIC": mentor_data.get("PROFILE_PIC")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/updateMentorProfileBanner")
        async def update_mentor_profile_banner(request: Request, MENTOR_ID:str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Profile Banner", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"PROFILE_BANNER": mentor_data.get("PROFILE_BANNER")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/UpdateMentorExperienceYears")
        async def update_mentor_experience_years(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Experience Years", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"EXPERIENCE_YEARS": mentor_data.get("EXPERIENCE_YEARS")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/UpdateMentorLocation")
        async def update_mentor_location(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Location", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"LOCATION": mentor_data.get("LOCATION")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/UpdateMentorBio")
        async def update_mentor_bio(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Bio", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"BIO": mentor_data.get("BIO")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

        @self.httpServer.app.put("/MentorProfile/UpdateMentorPricePerSession")
        async def update_mentor_price_per_session(request: Request, MENTOR_ID: str):
            try:
                mentor_data = await request.json()
                print("Updating Mentor Price Per Session", mentor_data)

                # Check if the mentor profile exists
                existing_mentor = self.mentor_profile_collection.find_one({"MENTOR_ID": MENTOR_ID})
                if not existing_mentor:
                    raise HTTPException(status_code=404, detail=f"Mentor profile with ID {MENTOR_ID} not found")

                # Update the mentor profile
                result = self.mentor_profile_collection.update_one(
                    {"MENTOR_ID": MENTOR_ID},
                    {"$set": {"PRICE_PER_SESSION": mentor_data.get("PRICE_PER_SESSION")}}
                )

                if result.modified_count == 0:
                    return {"message": "No changes were made to the mentor profile"}

                return {"message": "Mentor profile updated successfully"}
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error updating mentor profile: {str(e)}")

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
