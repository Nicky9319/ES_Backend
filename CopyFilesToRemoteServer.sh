# Mention the Files you want to transfer to the Remote Server alongiside with the Remote Server IP Address and the Remote Server Directory

# Example: 
# scp -r Logs/ \
#     ServiceTemplates/ \
#     ServicesSetupFiles/ \
#     ServiceURLMapping.json \
#     requirements.txt \
#     env.json \
#     Prompts/ \
#     ServerScripts/ \
#     \
#     service_LLMService/ \
#     service_LogService/ \
#     service_LoginService/ \
#     service_AvatarService/ \
#     service_ChatService/ \
#     service_MainServer/ \
#     service_TeamService/ \
#     service_ChromaDBService/ \
#     \
#     CreateCollection.py \
#     paarth@167.71.239.193:/home/paarth/MainServer/