"""
Seed script to populate the database with example documents and content.
This creates sample files with realistic content for testing search functionality.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backend.store import DocumentStore
    from backend.meilisearch_client import MeilisearchClient
except ImportError:
    from store import DocumentStore
    from meilisearch_client import MeilisearchClient

# Sample documents with realistic content
SAMPLE_DOCUMENTS = [
    {
        "filename": "invoice_acme_corp_2024.pdf",
        "type": "invoice",
        "size": "245 KB",
        "content": """
        INVOICE
        
        Invoice Number: INV-2024-001
        Date: January 15, 2024
        
        From:
        Acme Corporation
        123 Business Street
        San Francisco, CA 94105
        
        To:
        John Smith
        456 Customer Lane
        New York, NY 10001
        
        Description:
        - Professional Services (40 hours @ $150/hr): $6,000.00
        - Software License (Annual): $2,500.00
        - Support Package: $500.00
        
        Subtotal: $9,000.00
        Tax (8.5%): $765.00
        Total Amount Due: $9,765.00
        
        Payment Terms: Net 30
        Due Date: February 15, 2024
        """
    },
    {
        "filename": "receipt_grocery_store.jpg",
        "type": "receipt",
        "size": "128 KB",
        "content": """
        WHOLE FOODS MARKET
        Receipt #45678
        Date: March 10, 2024
        
        Items:
        - Organic Bananas (2 lbs): $3.98
        - Almond Milk: $4.99
        - Whole Grain Bread: $5.49
        - Free Range Eggs (dozen): $6.99
        - Greek Yogurt: $5.99
        - Fresh Spinach: $3.49
        - Chicken Breast (2 lbs): $14.98
        
        Subtotal: $45.91
        Tax: $3.21
        Total: $49.12
        
        Payment Method: Credit Card ending in 4532
        Thank you for shopping with us!
        """
    },
    {
        "filename": "medical_prescription_dr_jones.pdf",
        "type": "document",
        "size": "89 KB",
        "content": """
        MEDICAL PRESCRIPTION
        
        Patient: Sarah Johnson
        DOB: 05/12/1985
        Date: February 20, 2024
        
        Prescribing Physician: Dr. Robert Jones, MD
        Medical License: CA-12345
        
        Diagnosis: Seasonal Allergies
        
        Rx:
        1. Cetirizine 10mg - Take 1 tablet daily
           Quantity: 30 tablets
           Refills: 2
        
        2. Fluticasone Nasal Spray - Use twice daily
           Quantity: 1 bottle
           Refills: 1
        
        Instructions: Take medication with food. Avoid alcohol.
        
        Follow-up appointment scheduled for: April 20, 2024
        
        Dr. Robert Jones
        California Medical Center
        555-0123
        """
    },
    {
        "filename": "contract_employment_techcorp.pdf",
        "type": "document",
        "size": "312 KB",
        "content": """
        EMPLOYMENT AGREEMENT
        
        This Employment Agreement is entered into on January 1, 2024
        
        Between:
        TechCorp Industries Inc. ("Employer")
        789 Innovation Drive, Austin, TX 78701
        
        And:
        Michael Chen ("Employee")
        321 Residential Ave, Austin, TX 78702
        
        Position: Senior Software Engineer
        Department: Product Development
        Start Date: February 1, 2024
        
        Compensation:
        - Base Salary: $145,000 per year
        - Annual Bonus: Up to 20% of base salary
        - Stock Options: 5,000 shares vesting over 4 years
        
        Benefits:
        - Health Insurance (Medical, Dental, Vision)
        - 401(k) with 4% company match
        - 4 weeks PTO annually
        - Professional development budget: $3,000/year
        
        Work Schedule: Monday-Friday, flexible hours
        Remote Work: Hybrid (2 days office, 3 days remote)
        
        Both parties agree to the terms and conditions outlined herein.
        """
    },
    {
        "filename": "utility_bill_march_2024.pdf",
        "type": "document",
        "size": "156 KB",
        "content": """
        PACIFIC GAS & ELECTRIC
        Account Number: 987654321
        
        Billing Period: March 1 - March 31, 2024
        Service Address: 456 Maple Street, Oakland, CA 94601
        
        Electric Usage: 450 kWh
        Gas Usage: 25 Therms
        
        Charges:
        Electricity:
        - Generation: $67.50
        - Delivery: $42.30
        - Taxes & Fees: $8.75
        
        Natural Gas:
        - Commodity: $28.50
        - Transportation: $12.25
        - Taxes & Fees: $3.15
        
        Previous Balance: $0.00
        Current Charges: $162.45
        Total Amount Due: $162.45
        
        Due Date: April 22, 2024
        
        Pay online at www.pge.com or call 1-800-743-5000
        """
    },
    {
        "filename": "insurance_policy_auto.pdf",
        "type": "document",
        "size": "421 KB",
        "content": """
        AUTO INSURANCE POLICY
        
        Policy Number: AUTO-2024-556677
        Policy Period: June 1, 2024 - June 1, 2025
        
        Insured: Lisa Martinez
        Address: 789 Oak Drive, Los Angeles, CA 90001
        
        Vehicle Information:
        2022 Toyota Camry
        VIN: 1HGBH41JXMN109186
        
        Coverage:
        - Bodily Injury Liability: $250,000/$500,000
        - Property Damage Liability: $100,000
        - Collision: $500 deductible
        - Comprehensive: $500 deductible
        - Uninsured Motorist: $250,000/$500,000
        - Medical Payments: $5,000
        
        Premium Breakdown:
        - Liability: $850/year
        - Collision: $425/year
        - Comprehensive: $280/year
        
        Total Annual Premium: $1,555.00
        Monthly Payment: $129.58
        
        Claims: Call 1-800-CLAIM-01
        Roadside Assistance: 24/7 available
        """
    },
    {
        "filename": "tax_return_2023.pdf",
        "type": "document",
        "size": "589 KB",
        "content": """
        U.S. INDIVIDUAL INCOME TAX RETURN
        Form 1040 - Tax Year 2023
        
        Taxpayer: David Williams
        SSN: XXX-XX-6789
        Filing Status: Single
        
        Income:
        - Wages (W-2): $95,000
        - Interest Income: $450
        - Dividend Income: $1,200
        Total Income: $96,650
        
        Adjustments:
        - IRA Contribution: $6,500
        Adjusted Gross Income: $90,150
        
        Deductions:
        - Standard Deduction: $13,850
        Taxable Income: $76,300
        
        Tax Calculation:
        - Federal Income Tax: $13,457
        - Withholding: $14,250
        
        Refund: $793
        
        Direct Deposit: Account ending in 7890
        Expected Refund Date: April 30, 2024
        
        Prepared by: H&R Block
        Preparer ID: P12345678
        """
    },
    {
        "filename": "bank_statement_january_2024.pdf",
        "type": "document", 
        "size": "203 KB",
        "content": """
        CHASE BANK
        Monthly Statement - January 2024
        
        Account Holder: Emily Rodriguez
        Account Number: ****6543
        Statement Period: 01/01/2024 - 01/31/2024
        
        Beginning Balance: $8,542.16
        
        Deposits and Credits:
        01/05 - Direct Deposit (Salary): $4,200.00
        01/20 - Direct Deposit (Salary): $4,200.00
        Total Deposits: $8,400.00
        
        Withdrawals and Debits:
        01/03 - Rent Payment: $2,200.00
        01/08 - Grocery Store: $156.42
        01/12 - Gas Station: $65.00
        01/15 - Restaurant: $87.23
        01/22 - Utilities: $162.45
        01/28 - Credit Card Payment: $500.00
        Total Withdrawals: $3,171.10
        
        Ending Balance: $13,771.06
        
        Interest Earned: $2.35
        Service Charges: $0.00
        
        Customer Service: 1-800-935-9935
        """
    },
    {
        "filename": "meeting_notes_q1_planning.txt",
        "type": "document",
        "size": "45 KB",
        "content": """
        Q1 2024 PLANNING MEETING NOTES
        Date: December 15, 2023
        Attendees: Marketing Team
        
        Agenda:
        1. Review Q4 2023 Performance
        2. Set Q1 2024 Goals
        3. Budget Allocation
        4. Campaign Planning
        
        Key Discussion Points:
        
        Q4 Review:
        - Website traffic up 35% year-over-year
        - Social media engagement increased 50%
        - Email conversion rate: 3.2%
        - Customer acquisition cost: $45
        
        Q1 Goals:
        - Launch new product line in February
        - Increase email subscribers by 25%
        - Achieve 40% growth in organic traffic
        - Improve customer retention to 85%
        
        Budget:
        - Digital Advertising: $50,000
        - Content Creation: $25,000
        - Tools & Software: $10,000
        - Events & Sponsorships: $15,000
        Total Q1 Budget: $100,000
        
        Action Items:
        - Sarah: Finalize campaign calendar by 12/20
        - Mike: Set up new analytics dashboard
        - Jennifer: Research influencer partnerships
        - Team: Weekly check-ins every Monday 10am
        
        Next Meeting: January 8, 2024
        """
    },
    {
        "filename": "travel_itinerary_paris.pdf",
        "type": "document",
        "size": "178 KB",
        "content": """
        TRAVEL ITINERARY
        Destination: Paris, France
        Traveler: Jessica Thompson
        
        Outbound Flight:
        Date: May 15, 2024
        Flight: AF 083 (Air France)
        Departure: JFK New York - 6:30 PM
        Arrival: CDG Paris - 8:45 AM (May 16)
        Seat: 24A (Window)
        Confirmation: ABC123XYZ
        
        Hotel Accommodation:
        Hotel Le Meurice
        228 Rue de Rivoli, 75001 Paris
        Check-in: May 16, 2024 (3:00 PM)
        Check-out: May 22, 2024 (11:00 AM)
        Room Type: Deluxe Double
        Confirmation: HT567890
        
        Activities Booked:
        - Louvre Museum Tour: May 17, 10:00 AM
        - Eiffel Tower Summit: May 18, 6:00 PM
        - Versailles Day Trip: May 19, 9:00 AM
        - Seine River Dinner Cruise: May 20, 7:30 PM
        
        Return Flight:
        Date: May 22, 2024
        Flight: AF 084 (Air France)
        Departure: CDG Paris - 11:30 AM
        Arrival: JFK New York - 2:15 PM
        Seat: 18C (Aisle)
        
        Emergency Contact: +33 1 42 44 55 66
        Travel Insurance: Policy #TRV-2024-9876
        
        Important: Passport expires 2026
        """
    }
]

def seed_database():
    """Seed the database with example documents."""
    print("🌱 Starting database seeding...")
    
    # Initialize stores
    doc_store = DocumentStore()
    meili_client = MeilisearchClient(host="http://localhost:7700")
    
    try:
        # Setup Meilisearch index (keyword-only for now)
        meili_client.setup_index()
        print("✅ Meilisearch index configured")
    except Exception as e:
        print(f"⚠️  Meilisearch setup warning: {e}")
        print("Continuing with database seeding...")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("backend/uploads", exist_ok=True)
    
    documents_created = 0
    
    for sample in SAMPLE_DOCUMENTS:
        try:
            # Create a meaningful file path
            # For demo purposes, create .txt files so content is readable
            base_name = sample['filename'].rsplit('.', 1)[0]  # Remove extension
            file_path = f"backend/uploads/{base_name}.txt"
            
            # Write the actual content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{'=' * 80}\n")
                f.write(f"{sample['filename']}\n")
                f.write(f"{'=' * 80}\n\n")
                f.write(sample['content'].strip())
                f.write(f"\n\n{'=' * 80}\n")
                f.write(f"File Type: {sample['type']}\n")
                f.write(f"Size: {sample['size']}\n")
                f.write(f"{'=' * 80}\n")
            
            # Add document to SQLite
            doc_id = doc_store.add_document(
                filename=sample['filename'],
                path=file_path,
                type=sample['type'],
                size=sample['size'],
                parent_folder_id=None,  # All at root level
                content=sample['content']
            )
            
            print(f"✅ Created document: {sample['filename']} (ID: {doc_id})")
            print(f"   📁 File: {file_path}")
            
            # Index in Meilisearch
            try:
                meili_client.index_document(
                    doc_id=doc_id,
                    filename=sample['filename'],
                    content=sample['content'],
                    doc_type=sample['type'],
                    folder_id=None
                )
                print(f"   📇 Indexed in Meilisearch")
            except Exception as e:
                print(f"   ⚠️  Meilisearch indexing failed: {e}")
            
            documents_created += 1
            
        except Exception as e:
            print(f"❌ Error creating {sample['filename']}: {e}")
    
    print(f"\n🎉 Database seeding complete!")
    print(f"   Created {documents_created} documents")
    print(f"\n💡 Try searching for:")
    print(f"   - 'invoice' or 'payment'")
    print(f"   - 'medical' or 'prescription'")
    print(f"   - 'insurance' or 'policy'")
    print(f"   - 'travel' or 'Paris'")
    print(f"   - 'salary' or 'deposit'")

if __name__ == "__main__":
    seed_database()
