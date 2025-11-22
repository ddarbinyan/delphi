import os
import json
from typing import List, Dict, Any
from together import Together
from dotenv import load_dotenv

class DocumentChatbot:
    def __init__(self, api_key: str):
        """
        Initialize the chatbot with Together AI API key.
        
        Args:
            api_key: Together AI API key
        """
        self.client = Together(api_key=api_key)
        self.model = "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
        self.conversation_history = []
        
    def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search function to retrieve relevant documents.
        Replace this with your actual search implementation.
        
        Args:
            query: Search query from the user
            
        Returns:
            List of document dictionaries with 'title', 'summary', and 'content'
        """
        # PLACEHOLDER: Replace with your actual search logic
        # This could be vector search, keyword search, etc.
        
        # Example mock data
        mock_results = [
            {
            "title": "Mobile Phone Bill",
            "summary": "Monthly invoice from TelecomPlus for October 2023 with total amount of $89.50 due by November 15, 2023.",
            "content": "# TelecomPlus Mobile Invoice - October 2023\n\n## Account Summary\nAccount Number: TPL-7842-9912\nInvoice Date: October 25, 2023\nDue Date: November 15, 2023\n\n## Charges\n> Base Plan: Unlimited Talk & Text + 10GB Data: $65.00\n> Data Overage (2.3GB): $18.50\n> Device Protection Plan: $6.00\n\n## Total Amount Due: $89.50\n\nPayment Methods:\n- Online: portal.telecomplus.com\n- Phone: 1-800-TEL-PLUS\n- Mail: PO Box 1234, Chicago, IL 60601\n\nLate payments may result in service interruption and $15 late fee."
            },
            {
            "title": "Local Business Promotion Letter",
            "summary": "Community welcome package with discount coupons for local restaurants including Mario's Italian Bistro, Sunrise Cafe, and Thai Orchid.",
            "content": "# Welcome to Maple Creek Community!\n\n## Special Offers for New Residents\n\nWe've partnered with local businesses to welcome you to the neighborhood:\n\n### Restaurant Discounts\n- **Mario's Italian Bistro**: 20% off your first order\n  > 123 Main Street\n  > Code: WELCOME20\n  > Valid through: December 31, 2023\n\n- **Sunrise Cafe**: Free coffee with any breakfast purchase\n  > 456 Oak Avenue\n  > Code: SUNRISE2023\n  > Valid through: January 15, 2024\n\n- **Thai Orchid**: $15 off orders over $50\n  > 789 Elm Boulevard\n  > Code: MAPLECREEK15\n  > Valid through: February 28, 2024\n\nPresent this letter or use the codes above to redeem your discounts."
            },
            {
            "title": "Transport Subscription Notice",
            "summary": "Reminder from City Transit Authority about upcoming MetroPass subscription renewal with QR code for payment.",
            "content": "# City Transit Authority\n## Subscription Renewal Notice\n\nDear MetroPass Holder,\n\nYour monthly transit subscription will auto-renew on November 5, 2023.\n\n### Current Plan:\n> Unlimited Bus & Metro Access: $75.00/month\n\n### Payment Options:\n1. **QR Code Payment**: Scan the code below\n2. **Online**: citytransit.gov/payments\n3. **In Person**: Any transit station kiosk\n\n[QR CODE - Payment Portal: payments.citytransit.gov/MP-8842-7731]\n\nAccount: MP-8842-7731\nAmount: $75.00\nDue: November 5, 2023\n\nTo cancel auto-renewal, please visit your account settings before the due date."
            },
            {
            "title": "Bank Policy Update Letter",
            "summary": "Notification from First National Bank about changes in document processing procedures including new digital submission requirements and processing timelines.",
            "content": "# First National Bank\n## Important Policy Updates\n\nEffective January 1, 2024, we're updating our document processing procedures to serve you better.\n\n### Key Changes:\n\n#### Digital Submission Requirements\n> All loan applications must now be submitted through our secure portal at fnbportal.com\n> Physical documents will only be accepted for specific legal requirements\n\n#### Processing Timelines\n- **Standard Applications**: 3-5 business days (previously 5-7)\n- **Express Processing**: 24 hours (additional $25 fee applies)\n- **Mortgage Applications**: 10-14 business days\n\n#### Document Requirements\nAll submissions must include:\n- Completed application form\n- Government-issued ID\n- Proof of income (last 2 pay stubs or tax returns)\n- Address verification\n\nContact our customer service at 1-800-FNB-HELP or help@fnb.com with questions."
            },
            {
            "title": "University Tuition Invoice",
            "summary": "Fall 2023 tuition invoice from State University with total amount of $4,850.00 due by August 25, 2023.",
            "content": "# State University\n## Fall 2023 Tuition Invoice\n\nStudent: Johnathan Davis\nStudent ID: S-7742-2023\nInvoice Date: August 1, 2023\nDue Date: August 25, 2023\n\n### Charges\n- Tuition (12 credits): $4,200.00\n- Student Activity Fee: $150.00\n- Technology Fee: $75.00\n- Health Services Fee: $125.00\n- Library Fee: $75.00\n- Laboratory Fee (Chemistry): $225.00\n\n### Total Amount Due: $4,850.00\n\n### Payment Methods\n- Online: portal.stateuniversity.edu/payments\n- Bank Transfer: Routing #021000021, Account #7742991201\n- Payment Plan: Available through Student Accounts Office\n\n> Late payments will incur a 1.5% monthly fee and may prevent course registration.\n\nFinancial Aid Office: financialaid@stateuniversity.edu | (555) 123-4567"
            }
        ]
        
        print(f"🔍 Searching documents for: {query}")
        return mock_results
    
    def get_tools_definition(self) -> List[Dict]:
        """Define the search tool for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_documents",
                    "description": "Search through the document database to find relevant documents based on the user's query. Use this when the user asks questions about their documents.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query extracted from the user's question"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def format_documents_for_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into a readable context string."""
        if not documents:
            return "No relevant documents were found."
        
        context = "Retrieved Documents:\n\n"
        for i, doc in enumerate(documents, 1):
            context += f"Document {i}: {doc['title']}\n"
            context += f"Summary: {doc['summary']}\n\n"
        
        return context
    
    def chat(self, user_message: str) -> str:
        """
        Process a user message and return a response.
        
        Args:
            user_message: The user's question or message
            
        Returns:
            The chatbot's response
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Initial API call with function calling enabled
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions about documents. When a user asks about their documents, use the search_documents function to find relevant information. Then provide a clear, accurate answer based on the retrieved documents."
                },
                *self.conversation_history
            ],
            tools=self.get_tools_definition(),
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Check if the model wants to call a function
        if assistant_message.tool_calls:
            # Process function calls
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "search_documents":
                    # Call the search function
                    search_results = self.search_documents(function_args["query"])
                    
                    # Format the results
                    formatted_results = self.format_documents_for_context(search_results)
                    
                    # Add function response to conversation
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": formatted_results
                    })
            
            # Get final response with the search results
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions about documents. Use the document summaries provided to give accurate, relevant answers to the user's questions."
                    },
                    *self.conversation_history
                ]
            )
            
            final_answer = final_response.choices[0].message.content
            
            # Add final response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_answer
            })
            
            return final_answer
        else:
            # No function call needed, return direct response
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content
            })
            return assistant_message.content
    
    def reset_conversation(self):
        """Clear the conversation history."""
        self.conversation_history = []


# Example usage
if __name__ == "__main__":
    # Initialize the chatbot
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')  # Set your API key as environment variable
    chatbot = DocumentChatbot(api_key)
    
    if not api_key:
        print("❌ Error: TOGETHER_API_KEY environment variable not set!")
        print("Please set it with: export TOGETHER_API_KEY='your-api-key'")
        exit(1)
    
    chatbot = DocumentChatbot(api_key)
    
    print("=" * 60)
    print("🤖 Document Chat System - Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your questions naturally")
    print("  - Type 'reset' to clear conversation history")
    print("  - Type 'history' to see conversation history")
    print("  - Type 'quit' or 'exit' to end the session")
    print("\n" + "=" * 60 + "\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            elif user_input.lower() == 'reset':
                chatbot.reset_conversation()
                print("✅ Conversation history cleared!\n")
                continue
            
            elif user_input.lower() == 'history':
                print("\n📜 Conversation History:")
                print("-" * 60)
                if not chatbot.conversation_history:
                    print("(No conversation yet)")
                else:
                    for msg in chatbot.conversation_history:
                        role = msg.get("role", "unknown").upper()
                        content = msg.get("content", "")
                        if content:
                            print(f"{role}: {content[:200]}...")
                print("-" * 60 + "\n")
                continue
            
            # Process the question
            print("\n🤔 Processing...\n")
            response = chatbot.chat(user_input)
            print(f"Assistant: {response}\n")
            print("-" * 60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            continue