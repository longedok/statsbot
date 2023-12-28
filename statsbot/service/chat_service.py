from dao import chat_dao


class ChatService:
    def create_chat(self, chat_dto):
        await chat_dao.create_chat()

chat_service = ChatService()

